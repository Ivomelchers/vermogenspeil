"""CSV-detectie, preview en import (alle brokers)."""

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.utils.responses import api_error, api_response
from apps.integrations.api_helpers import linked_user_or_error, require_verified_email
from apps.integrations.csv.base import CsvParseError
from apps.integrations.csv.detection import detect_csv_platform
from apps.integrations.csv.import_service import import_csv_for_user
from apps.integrations.csv.preview import preview_csv_for_user
from apps.integrations.csv.registry import list_csv_platforms
from apps.integrations.csv.upload_io import read_csv_upload


class CsvPlatformsListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error
        return api_response(data={"platforms": list_csv_platforms()})


class CsvDetectView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error
        if err := require_verified_email(user):
            return err

        content, read_error = read_csv_upload(request)
        if read_error:
            return read_error

        try:
            matches = detect_csv_platform(content)
        except CsvParseError as exc:
            return api_error(
                message=str(exc),
                error="csv_detect_failed",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return api_response(
            data={
                "matches": [
                    {
                        "platform": m.platform,
                        "platform_display": m.platform_display,
                        "confidence": m.confidence,
                        "missing_headers": m.missing_headers,
                    }
                    for m in matches
                ],
                "recommended": matches[0].platform if matches else None,
            },
            message="CSV geanalyseerd.",
        )


class CsvPreviewView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error
        if err := require_verified_email(user):
            return err

        content, read_error = read_csv_upload(request)
        if read_error:
            return read_error

        platform = (request.data.get("platform") or "").strip() or None
        result = preview_csv_for_user(user, content, platform=platform)

        if result["status"] == "rejected":
            return api_response(data=result, message=result["message"])

        return api_response(
            data=result,
            message=(
                f"Preview: {result['summary']['new']} nieuw, "
                f"{result['summary']['duplicate']} al aanwezig."
            ),
        )


class CsvImportView(APIView):
    """Enige import-endpoint voor CSV (DEGIRO en toekomstige brokers)."""

    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        user, error = linked_user_or_error(request)
        if error:
            return error
        if err := require_verified_email(user):
            return err

        content, read_error = read_csv_upload(request)
        if read_error:
            return read_error

        platform = (request.data.get("platform") or "").strip() or None
        label = request.data.get("label")

        try:
            result = import_csv_for_user(
                user,
                content,
                platform=platform,
                label=label,
            )
        except CsvParseError as exc:
            return api_error(
                message=str(exc),
                error="csv_import_failed",
                status=status.HTTP_400_BAD_REQUEST,
            )

        message = result.get("trust_summary") or "CSV geïmporteerd."
        if result.get("has_import_gaps"):
            message += " Niet alle regels zijn verwerkt — zie importrapport."

        return api_response(
            data=result,
            message=message,
            status=status.HTTP_201_CREATED,
        )
