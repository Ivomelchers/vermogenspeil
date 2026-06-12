from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from django.shortcuts import redirect
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import requests
import logging

from apps.accounts.utils.responses import api_error, api_response, first_validation_message
from apps.integrations.base import PlatformAdapterError
from apps.integrations.bitvavo.adapter import BitvavoPlatformAdapter
from apps.integrations.bybit.adapter import BybitPlatformAdapter
from apps.integrations.okx.adapter import OkxPlatformAdapter
from apps.integrations.trading212.adapter import Trading212Adapter
from apps.integrations.saxo.adapter import SaxoPlatformAdapter
from apps.integrations.models import (
    ConnectionMethod,
    PlatformConnection,
    PlatformType,
    SyncJob,
    SyncStatus,
)
from apps.integrations.serializers import (
    BitvavoConnectSerializer,
    BybitConnectSerializer,
    OkxConnectSerializer,
    Trading212ConnectSerializer,
    PlatformConnectionSerializer,
    PlatformImportBatchSerializer,
    SyncJobSerializer,
)
from apps.integrations.services.import_batches import purge_connection_data, purge_import_batch
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.api_helpers import linked_user_or_error, require_verified_email
from apps.integrations.services.demo_seed import demo_features_enabled, seed_demo_for_user
from apps.integrations.tasks import sync_platform_connection
from apps.portfolio.services import get_or_create_default_portfolio

logger = logging.getLogger(__name__)


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


class BybitConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error

        verified_error = require_verified_email(user)
        if verified_error:
            return verified_error

        serializer = BybitConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        portfolio = get_or_create_default_portfolio(user)
        label = data.get("label") or "Bybit"

        connection, created = PlatformConnection.objects.get_or_create(
            user=user,
            platform=PlatformType.BYBIT,
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
            BybitPlatformAdapter(connection).validate_connection()
        except PlatformAdapterError as exc:
            connection.is_active = False
            connection.status = SyncStatus.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["is_active", "status", "last_error", "updated_at"])
            return api_error(
                message=str(exc),
                error="bybit_connection_failed",
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
            message="Bybit gekoppeld. Synchronisatie is gestart.",
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class OkxConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error

        verified_error = require_verified_email(user)
        if verified_error:
            return verified_error

        serializer = OkxConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        portfolio = get_or_create_default_portfolio(user)
        label = data.get("label") or "OKX"
        domain = data.get("domain", "okx.com")

        connection, created = PlatformConnection.objects.get_or_create(
            user=user,
            platform=PlatformType.OKX,
            label=label,
            defaults={
                "portfolio": portfolio,
                "connection_method": ConnectionMethod.API,
                "status": SyncStatus.PENDING,
                "okx_domain": domain,
            },
        )

        if not created:
            connection.portfolio = portfolio
            connection.is_active = True
            connection.okx_domain = domain
            connection.save(update_fields=["portfolio", "is_active", "okx_domain", "updated_at"])

        store_api_credentials(
            connection,
            api_key=data["api_key"],
            api_secret=data["api_secret"],
            api_passphrase=data["api_passphrase"],
        )

        try:
            OkxPlatformAdapter(connection).validate_connection()
        except PlatformAdapterError as exc:
            connection.is_active = False
            connection.status = SyncStatus.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["is_active", "status", "last_error", "updated_at"])
            return api_error(
                message=str(exc),
                error="okx_connection_failed",
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
            message="OKX gekoppeld. Synchronisatie is gestart.",
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class Trading212ConnectView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error

        verified_error = require_verified_email(user)
        if verified_error:
            return verified_error

        serializer = Trading212ConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        portfolio = get_or_create_default_portfolio(user)
        label = data.get("label") or "Trading 212"

        connection, created = PlatformConnection.objects.get_or_create(
            user=user,
            platform=PlatformType.TRADING212,
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
            api_secret="",
        )

        try:
            Trading212Adapter(connection).validate_connection()
        except PlatformAdapterError as exc:
            connection.is_active = False
            connection.status = SyncStatus.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["is_active", "status", "last_error", "updated_at"])
            return api_error(
                message=str(exc),
                error="trading212_connection_failed",
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
            message="Trading 212 gekoppeld. Synchronisatie is gestart.",
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
        connection.api_passphrase_encrypted = ""
        connection.save(
            update_fields=[
                "is_active",
                "api_key_encrypted",
                "api_secret_encrypted",
                "api_passphrase_encrypted",
                "updated_at",
            ]
        )
        return api_response(
            message=(
                "Platform losgekoppeld. Uw geïmporteerde transacties blijven bewaard. "
                "Gebruik 'Alle data wissen' om importdata te verwijderen."
            ),
        )


class PlatformConnectionPurgeDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id):
        user, error = linked_user_or_error(request)
        if error:
            return error

        try:
            result = purge_connection_data(user, connection_id)
        except LookupError:
            return api_error(
                message="Koppeling niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        return api_response(
            data=result,
            message=(
                f"{result['transactions_deleted']} transactie(s) verwijderd "
                f"({result['import_batches_deleted']} import(s))."
            ),
        )


class PlatformImportBatchListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, connection_id):
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

        batches = connection.import_batches.all()
        serializer = PlatformImportBatchSerializer(batches, many=True)
        return api_response(data=serializer.data)


class PlatformImportBatchPurgeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, batch_id):
        user, error = linked_user_or_error(request)
        if error:
            return error

        try:
            result = purge_import_batch(user, batch_id)
        except LookupError:
            return api_error(
                message="Import niet gevonden.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        return api_response(
            data=result,
            message=f"{result['transactions_deleted']} transactie(s) uit deze import verwijderd.",
        )


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


class OkxValidateCredentialsView(APIView):
    """Test OKX credentials zonder opslaan (diagnostisch)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error

        serializer = OkxConnectSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        domain = data.get("domain", "okx.com")

        # Maak een temporaire connection om te testen
        temp_connection = PlatformConnection(
            user=user,
            platform=PlatformType.OKX,
            connection_method=ConnectionMethod.API,
            status=SyncStatus.PENDING,
            okx_domain=domain,
        )

        # Sla credentials op (versleuteld) maar commit niet
        from apps.integrations.services.credentials import store_api_credentials
        store_api_credentials(
            temp_connection,
            api_key=data["api_key"],
            api_secret=data["api_secret"],
            api_passphrase=data["api_passphrase"],
        )

        try:
            adapter = OkxPlatformAdapter(temp_connection)
            adapter.validate_connection()
            return api_response(
                data={
                    "valid": True,
                    "message": f"OKX credentials zijn geldig op {domain}.",
                    "domain": domain,
                },
                status=status.HTTP_200_OK,
            )
        except PlatformAdapterError as exc:
            return api_response(
                data={
                    "valid": False,
                    "error_message": str(exc),
                    "domain": domain,
                },
                status=status.HTTP_200_OK,  # 200 maar valid=False (geen 4xx error)
            )


@method_decorator(login_required(login_url="/auth/login"), name="dispatch")
class SaxoOAuthCallbackView(View):
    """Handle OAuth2 callback from Saxo Bank."""

    def get(self, request):
        code = request.GET.get("code")
        state = request.GET.get("state")
        error = request.GET.get("error")
        error_description = request.GET.get("error_description")

        logger.info(f"Saxo OAuth callback received for user {request.user.id}")

        if error:
            logger.warning(f"Saxo OAuth error: {error} - {error_description}")
            return redirect(f"/auth/saxo/callback-error?error={error}&description={error_description}")

        if not code:
            logger.warning("Saxo OAuth callback received without authorization code")
            return redirect("/auth/saxo/callback-error?error=missing_code&description=Authorization code not received")

        user = request.user

        # Exchange authorization code for access token
        logger.info(f"Exchanging Saxo authorization code for access token (user: {user.id})")
        try:
            token_response = self._exchange_code_for_token(code)
            logger.info(f"Token exchange succeeded: got access_token and refresh_token (user: {user.id})")
        except Exception as exc:
            logger.error(f"Saxo OAuth token exchange failed: {exc}", exc_info=True)
            return redirect("/auth/saxo/callback-error?error=token_exchange_failed&description=Token exchange failed")

        if not token_response:
            logger.error("Token response is empty")
            return redirect("/auth/saxo/callback-error?error=invalid_token_response&description=Invalid token response")

        # Create or update PlatformConnection
        logger.info(f"Creating/updating Saxo PlatformConnection (user: {user.id})")
        try:
            connection = self._create_or_update_connection(
                user=user,
                access_token=token_response.get("access_token"),
                refresh_token=token_response.get("refresh_token"),
            )
            logger.info(f"Connection created/updated: ID={connection.id} (user: {user.id})")
        except Exception as exc:
            logger.error(f"Saxo connection creation failed: {exc}", exc_info=True)
            return redirect("/auth/saxo/callback-error?error=connection_failed&description=Failed to create connection")

        # Validate the connection
        logger.info(f"Validating Saxo connection (connection: {connection.id}, user: {user.id})")
        try:
            SaxoPlatformAdapter(connection).validate_connection()
            logger.info(f"Connection validation succeeded (connection: {connection.id})")
        except PlatformAdapterError as exc:
            connection.is_active = False
            connection.status = SyncStatus.ERROR
            connection.last_error = str(exc)
            connection.save(update_fields=["is_active", "status", "last_error", "updated_at"])
            logger.error(f"Saxo connection validation failed: {exc}")
            return redirect("/auth/saxo/callback-error?error=validation_failed&description=Connection validation failed")

        # Start sync job
        logger.info(f"Starting sync job for Saxo connection (connection: {connection.id})")
        try:
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
            logger.info(f"Sync job created (job: {sync_job.id}, connection: {connection.id})")
        except Exception as exc:
            logger.error(f"Saxo sync job creation failed: {exc}", exc_info=True)
            # Don't fail, connection is already valid

        logger.info(f"Saxo OAuth callback completed successfully (connection: {connection.id}, user: {user.id})")
        return redirect(f"/auth/saxo/callback-success?connection_id={connection.id}")

    def _exchange_code_for_token(self, code: str) -> dict | None:
        """Exchange authorization code for access token."""
        from django.conf import settings

        token_endpoint = "https://sim.logonvalidation.net/token"
        client_id = getattr(settings, "SAXO_CLIENT_ID", "")
        client_secret = getattr(settings, "SAXO_CLIENT_SECRET", "")

        # Get the correct redirect_uri based on the request
        if self.request.is_secure():
            scheme = "https"
        else:
            scheme = "http"
        redirect_uri = f"{scheme}://{self.request.get_host()}/auth/saxo/callback/"

        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
        }

        try:
            response = requests.post(token_endpoint, data=data, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            logger.error(f"Token endpoint error: {exc}")
            raise

    def _create_or_update_connection(self, user, access_token: str, refresh_token: str | None = None) -> PlatformConnection:
        """Create or update Saxo platform connection."""
        portfolio = get_or_create_default_portfolio(user)

        connection, created = PlatformConnection.objects.get_or_create(
            user=user,
            platform=PlatformType.SAXO,
            label="Saxo Bank",
            defaults={
                "portfolio": portfolio,
                "connection_method": ConnectionMethod.OAUTH,
                "status": SyncStatus.PENDING,
            },
        )

        if not created:
            connection.portfolio = portfolio
            connection.is_active = True
            connection.connection_method = ConnectionMethod.OAUTH
            connection.save(update_fields=["portfolio", "is_active", "connection_method", "updated_at"])

        # Store tokens encrypted
        store_api_credentials(
            connection,
            api_key=access_token,  # Store access_token as api_key
            api_secret=refresh_token or "",  # Store refresh_token as api_secret
        )

        return connection


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
