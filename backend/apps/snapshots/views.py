from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.utils.responses import api_error, api_response
from apps.snapshots.exceptions import SnapshotAlreadyExistsError
from apps.snapshots.models import PeilDatumSnapshot
from apps.snapshots.serializers import (
    PeilDatumSnapshotCreateSerializer,
    PeilDatumSnapshotSerializer,
)
from apps.snapshots.services.peildatum import create_peildatum_snapshot


def _linked_user_or_error(request):
    user = request.user
    if not user or not user.is_authenticated:
        return None, api_error(
            message="Authenticatie vereist.",
            error="unauthorized",
            status=status.HTTP_401_UNAUTHORIZED,
        )
    return user, None


class PeilDatumSnapshotListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        snapshots = PeilDatumSnapshot.objects.filter(user=user).order_by("-year")
        return api_response(
            data=PeilDatumSnapshotSerializer(snapshots, many=True).data,
            message=f"{snapshots.count()} snapshot(s)",
        )


class PeilDatumSnapshotDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, year: int):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        snapshot = PeilDatumSnapshot.objects.filter(user=user, year=year).first()
        if not snapshot:
            return api_error(
                message=f"Geen peildatum-snapshot voor {year}.",
                error="not_found",
                status=status.HTTP_404_NOT_FOUND,
            )

        return api_response(data=PeilDatumSnapshotSerializer(snapshot).data)


class PeilDatumSnapshotCreateView(APIView):
    """Handmatige snapshot voor testen (immutable na creatie)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        serializer = PeilDatumSnapshotCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        year = serializer.validated_data["year"]

        try:
            snapshot = create_peildatum_snapshot(user, year)
        except SnapshotAlreadyExistsError as exc:
            return api_error(
                message=str(exc),
                error="snapshot_exists",
                status=status.HTTP_409_CONFLICT,
            )

        return api_response(
            data=PeilDatumSnapshotSerializer(snapshot).data,
            message=f"Peildatum-snapshot {year} vastgelegd.",
            status=status.HTTP_201_CREATED,
        )
