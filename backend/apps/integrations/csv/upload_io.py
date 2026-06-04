"""CSV-upload lezen (gedeeld door alle CSV-endpoints)."""

from rest_framework import status

from apps.accounts.utils.responses import api_error


def read_csv_upload(request):
    upload = request.FILES.get("file")
    if not upload:
        return None, api_error(
            message="Geen bestand ontvangen. Upload veld: file",
            error="missing_file",
            status=status.HTTP_400_BAD_REQUEST,
        )
    try:
        return upload.read().decode("utf-8-sig"), None
    except UnicodeDecodeError:
        return None, api_error(
            message="CSV moet UTF-8 tekst zijn.",
            error="invalid_encoding",
            status=status.HTTP_400_BAD_REQUEST,
        )
