from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.utils.responses import api_error, api_response, first_validation_message
from apps.integrations.base import PlatformAdapterError
from apps.integrations.bitvavo.adapter import BitvavoPlatformAdapter
from apps.integrations.models import (
    ConnectionMethod,
    PlatformConnection,
    PlatformType,
    SyncJob,
    SyncStatus,
)
from apps.integrations.serializers import (
    BitvavoConnectSerializer,
    PlatformConnectionSerializer,
    SyncJobSerializer,
)
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.api_helpers import linked_user_or_error, require_verified_email
from apps.integrations.services.demo_seed import demo_features_enabled, seed_demo_for_user
from apps.integrations.tasks import sync_platform_connection
from apps.portfolio.services import get_or_create_default_portfolio


class PlatformConnectionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error

        connections = PlatformConnection.objects.for_user(user).filter(is_active=True)
        if not demo_features_enabled():
            connections = connections.filter(is_demo=False)
        serializer = PlatformConnectionSerializer(connections, many=True)
        return api_response(data=serializer.data)


class BitvavoConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error

        verified_error = require_verified_email(user)
        if verified_error:
            return verified_error

        serializer = BitvavoConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        portfolio = get_or_create_default_portfolio(user)
        label = data.get("label") or "Bitvavo"

        connection, created = PlatformConnection.objects.get_or_create(
            user=user,
            platform=PlatformType.BITVAVO,
            label=label,
            defaults={
                "portfolio": portfolio,
                "connection_method": ConnectionMethod.API,
                "status": SyncStatus.PENDING,
            },
        )

        if not created:
            connection.portfolio = portfolio
            connection.is_active = True
            connection.save(update_fields=["portfolio", "is_active", "updated_at"])

        store_api_credentials(
            connection,
            api_key=data["api_key"],
            api_secret=data["api_secret"],
        )

        try:
            BitvavoPlatformAdapter(connection).validate_connection()
        except PlatformAdapterError as exc:
            connection.is_active = False
            connection.status = SyncStatus.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["is_active", "status", "last_error", "updated_at"])
            return api_error(
                message=str(exc),
                error="bitvavo_connection_failed",
                status=status.HTTP_400_BAD_REQUEST,
            )

        connection.status = SyncStatus.PENDING
        connection.last_error = ""
        connection.save(update_fields=["status", "last_error", "updated_at"])

        sync_job = SyncJob.objects.create(
            connection=connection,
            status=SyncStatus.PENDING,
        )
        task = sync_platform_connection.delay(sync_job.id)
        sync_job.celery_task_id = task.id
        sync_job.save(update_fields=["celery_task_id"])

        response_data = PlatformConnectionSerializer(connection).data
        response_data["sync_job"] = SyncJobSerializer(sync_job).data
        return api_response(
            data=response_data,
            message="Bitvavo gekoppeld. Synchronisatie is gestart.",
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PlatformConnectionDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, connection_id):
        user, error = linked_user_or_error(request)
        if error:
            return error

        connection = PlatformConnection.objects.for_user(user).filter(pk=connection_id).first()
        if not connection:
            return api_error(
                message="Koppeling niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        connection.is_active = False
        connection.api_key_encrypted = ""
        connection.api_secret_encrypted = ""
        connection.save(
            update_fields=[
                "is_active",
                "api_key_encrypted",
                "api_secret_encrypted",
                "updated_at",
            ]
        )
        return api_response(message="Platformkoppeling verwijderd.")


class PlatformSyncView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id):
        user, error = linked_user_or_error(request)
        if error:
            return error

        verified_error = require_verified_email(user)
        if verified_error:
            return verified_error

        connection = PlatformConnection.objects.for_user(user).filter(pk=connection_id).first()
        if not connection or not connection.is_active:
            return api_error(
                message="Koppeling niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        sync_job = SyncJob.objects.create(
            connection=connection,
            status=SyncStatus.PENDING,
        )
        task = sync_platform_connection.delay(sync_job.id)
        sync_job.celery_task_id = task.id
        sync_job.save(update_fields=["celery_task_id"])

        return api_response(
            data=SyncJobSerializer(sync_job).data,
            message="Synchronisatie gestart.",
            status=status.HTTP_202_ACCEPTED,
        )


class SyncJobDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        user, error = linked_user_or_error(request)
        if error:
            return error

        sync_job = (
            SyncJob.objects.select_related("connection")
            .filter(connection__user=user, pk=job_id)
            .first()
        )
        if not sync_job:
            return api_error(
                message="Sync-taak niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        return api_response(data=SyncJobSerializer(sync_job).data)


class DemoFeaturesStatusView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return api_response(data={"enabled": demo_features_enabled()})


class DemoSeedView(APIView):
    """Laad voorbeeldportefeuille — alleen als DEMO_FEATURES_ENABLED (development)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not demo_features_enabled():
            return api_error(
                message="Demo-functies zijn niet beschikbaar.",
                error="demo_disabled",
                status=status.HTTP_404_NOT_FOUND,
            )

        user, error = linked_user_or_error(request)
        if error:
            return error

        try:
            result = seed_demo_for_user(user)
        except PermissionError:
            return api_error(
                message="Demo-functies zijn niet beschikbaar.",
                error="demo_disabled",
                status=status.HTTP_404_NOT_FOUND,
            )

        return api_response(
            data=result,
            message=(
                "Voorbeelddata geladen: Bitvavo en DEGIRO (demo). "
                "Geen echte broker-accounts nodig."
            ),
        )
