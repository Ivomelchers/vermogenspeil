from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from apps.accounts.serializers import (
    RegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
)
from apps.accounts.services.verification import resend_verification_email, verify_email_token
from apps.accounts.utils.responses import api_error, api_response, first_validation_message


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = serializer.save()
        return api_response(
            data={
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "email_verified": user.email_verified,
            },
            message="Registratie gelukt. Bevestig je e-mailadres via de link in je inbox.",
            status=status.HTTP_201_CREATED,
        )


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = verify_email_token(serializer.validated_data["token"])
        except ValueError as exc:
            error_code = str(exc)
            if error_code == "expired_token":
                return api_error(
                    message="De verificatielink is verlopen. Vraag een nieuwe aan.",
                    error="expired_token",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            return api_error(
                message="Ongeldige verificatielink.",
                error="invalid_token",
                status=status.HTTP_400_BAD_REQUEST,
            )

        return api_response(
            data={
                "email": user.email,
                "email_verified": user.email_verified,
            },
            message="E-mailadres bevestigd. Je kunt nu inloggen.",
        )


class ResendVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        resend_verification_email(serializer.validated_data["email"])
        return api_response(
            message="Als dit e-mailadres bij ons bekend is, ontvang je een nieuwe verificatielink.",
        )
