from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.authentication import UnlinkedAuth0User, reset_mfa
from apps.accounts.serializers import (
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from apps.accounts.services.auth0_login import Auth0LoginError, exchange_password, exchange_refresh_token
from apps.accounts.services.password_reset import (
    request_password_reset,
    reset_password,
    validate_password_reset_token,
)
from apps.accounts.services.verification import resend_verification_email, verify_email_token
from apps.accounts.models import User
from apps.accounts.utils.responses import api_error, api_response, first_validation_message


def _handle_value_error(exc, mapping):
    error_code = str(exc)
    if error_code in mapping:
        message, status_code = mapping[error_code]
        return api_error(message=message, error=error_code, status=status_code)
    return api_error(message="Er is iets misgegaan.", error="error", status=400)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

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
    authentication_classes = []

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
    authentication_classes = []

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


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is None:
            return api_error(
                message="Ongeldige inloggegevens.",
                error="invalid_credentials",
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.email_verified:
            return api_error(
                message="Bevestig eerst je e-mailadres voordat je inlogt.",
                error="email_not_verified",
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            tokens = exchange_password(email, password)
        except Auth0LoginError as exc:
            return api_error(
                message=exc.message,
                error=exc.error,
                data=exc.data or None,
                status=exc.status_code,
            )

        return api_response(data=tokens, message="Ingelogd.")


class TokenRefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RefreshTokenSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            tokens = exchange_refresh_token(serializer.validated_data["refresh"])
        except Auth0LoginError as exc:
            return api_error(
                message=exc.message,
                error=exc.error,
                status=exc.status_code,
            )

        return api_response(data=tokens, message="Token vernieuwd.")


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if isinstance(user, UnlinkedAuth0User):
            return api_error(
                message="Account niet gekoppeld. Neem contact op met support.",
                error="account_not_linked",
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.email_verified:
            return api_error(
                message="Bevestig eerst je e-mailadres.",
                error="email_not_verified",
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = UserSerializer(user)
        return api_response(data=serializer.data, message="Profiel opgehaald.")


class ResetAuthenticatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        reset_mfa(request.user)
        return api_response(message="Authenticator gereset. Stel 2FA opnieuw in bij de volgende login.")


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_password_reset(serializer.validated_data["email"])
        return api_response(
            message="Als dit e-mailadres bij ons bekend is, ontvangt u een resetlink.",
        )


class PasswordResetTokenView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request, token):
        try:
            user = validate_password_reset_token(token)
        except ValueError as exc:
            return _handle_value_error(
                exc,
                {
                    "invalid_token": (
                        "Ongeldige resetlink.",
                        status.HTTP_400_BAD_REQUEST,
                    ),
                    "expired_token": (
                        "De resetlink is verlopen. Vraag een nieuwe aan.",
                        status.HTTP_400_BAD_REQUEST,
                    ),
                },
            )

        return api_response(
            data={"email": user.email},
            message="Resetlink is geldig.",
        )

    def post(self, request, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = reset_password(token, serializer.validated_data["password"])
        except ValueError as exc:
            return _handle_value_error(
                exc,
                {
                    "invalid_token": (
                        "Ongeldige resetlink.",
                        status.HTTP_400_BAD_REQUEST,
                    ),
                    "expired_token": (
                        "De resetlink is verlopen. Vraag een nieuwe aan.",
                        status.HTTP_400_BAD_REQUEST,
                    ),
                },
            )

        return api_response(
            data={"email": user.email},
            message="Wachtwoord bijgewerkt. U kunt nu inloggen.",
        )
