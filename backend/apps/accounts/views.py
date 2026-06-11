from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import json

from apps.accounts.serializers import (
    LoginSerializer,
    MfaLoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    RefreshTokenSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    TwoFactorDisableSerializer,
    TwoFactorVerifySerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from apps.accounts.utils.rate_limit import rate_limit
from apps.accounts.services.auth0_login import (
    Auth0LoginError,
    exchange_password,
    exchange_refresh_token,
)
from apps.accounts.services.password_reset import (
    request_password_reset,
    reset_password,
    validate_password_reset_token,
)
from apps.accounts.services.totp import (
    complete_mfa_login,
    confirm_totp_setup,
    create_mfa_login_challenge,
    disable_totp,
    get_user_2fa_status,
    start_totp_setup,
    verify_user_otp,
)
from apps.accounts.services.password_reset import (
    request_password_reset,
    reset_password,
    validate_password_reset_token,
)
from apps.accounts.services.verification import resend_verification_email, verify_email_token
from apps.accounts.authentication import UnlinkedAuth0User, auth0_sub_from_id_token
from apps.accounts.models import User
from apps.accounts.utils.responses import api_error, api_response, first_validation_message


def _handle_value_error(exc, mapping):
    error_code = str(exc)
    if error_code in mapping:
        message, status_code = mapping[error_code]
        return api_error(message=message, error=error_code, status=status_code)
    return api_error(message="Er is iets misgegaan.", error="error", status=400)


def _linked_user_or_error(request):
    user = request.user
    if isinstance(user, UnlinkedAuth0User):
        return None, api_error(
            message="Account niet gekoppeld. Neem contact op met support.",
            error="account_not_linked",
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @rate_limit(limit_per_minute=3)
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

    @rate_limit(limit_per_minute=5)
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

        token_sub = auth0_sub_from_id_token(tokens["id_token"])
        if user.auth_0_id != token_sub:
            user.auth_0_id = token_sub
            user.save(update_fields=["auth_0_id"])

        if user.is_2fa_enabled:
            challenge = create_mfa_login_challenge(user, tokens)
            return api_error(
                message="Voer uw tweefactorcode in.",
                error="mfa_required",
                data={"mfa_token": challenge.token},
                status=status.HTTP_403_FORBIDDEN,
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

    def _linked_user_or_error(self, request):
        user = request.user
        if isinstance(user, UnlinkedAuth0User):
            return None, api_error(
                message="Account niet gekoppeld. Neem contact op met support.",
                error="account_not_linked",
                status=status.HTTP_403_FORBIDDEN,
            )
        if not user.email_verified:
            return None, api_error(
                message="Bevestig eerst je e-mailadres.",
                error="email_not_verified",
                status=status.HTTP_403_FORBIDDEN,
            )
        return user, None

    def get(self, request):
        user, error = self._linked_user_or_error(request)
        if error:
            return error
        serializer = UserSerializer(user)
        return api_response(data=serializer.data, message="Profiel opgehaald.")

    def patch(self, request):
        user, error = self._linked_user_or_error(request)
        if error:
            return error
        from apps.accounts.serializers import UserProfileUpdateSerializer

        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save()
        return api_response(
            data=UserSerializer(user).data,
            message="Profiel bijgewerkt.",
        )

    def delete(self, request):
        user, error = self._linked_user_or_error(request)
        if error:
            return error

        from apps.accounts.serializers import AccountDeleteSerializer
        from apps.accounts.services.account_deletion import soft_delete_user

        serializer = AccountDeleteSerializer(
            data=request.data,
            context={"user": user},
        )
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        soft_delete_user(user)
        return api_response(
            data=None,
            message="Uw account is verwijderd. U bent uitgelogd.",
            status=status.HTTP_200_OK,
        )


class MfaStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error_response = _linked_user_or_error(request)
        if error_response:
            return error_response

        return api_response(
            data=get_user_2fa_status(user),
            message="2FA-status opgehaald.",
        )


class TwoFactorSetupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error_response = _linked_user_or_error(request)
        if error_response:
            return error_response

        try:
            setup_data = start_totp_setup(user)
        except ValueError as exc:
            if str(exc) == "already_enabled":
                return api_error(
                    message="2FA is al actief op uw account.",
                    error="already_enabled",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise

        return api_response(
            data=setup_data,
            message="Scan de QR-code en bevestig met een verificatiecode.",
        )


class TwoFactorVerifyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error_response = _linked_user_or_error(request)
        if error_response:
            return error_response

        serializer = TwoFactorVerifySerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            backup_codes = confirm_totp_setup(user, serializer.validated_data["otp"])
        except ValueError as exc:
            error_code = str(exc)
            if error_code == "invalid_otp":
                return api_error(
                    message="Ongeldige verificatiecode.",
                    error="invalid_otp",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if error_code == "setup_not_started":
                return api_error(
                    message="Start eerst de 2FA-setup.",
                    error="setup_not_started",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if error_code == "already_enabled":
                return api_error(
                    message="2FA is al actief op uw account.",
                    error="already_enabled",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            raise

        return api_response(
            data={"backup_codes": backup_codes},
            message="2FA is geactiveerd. Bewaar uw backupcodes op een veilige plek.",
        )


class TwoFactorDisableView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error_response = _linked_user_or_error(request)
        if error_response:
            return error_response

        serializer = TwoFactorDisableSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        password = serializer.validated_data["password"]
        otp = serializer.validated_data["otp"]

        try:
            exchange_password(user.email, password)
        except Auth0LoginError as exc:
            if exc.error == "invalid_credentials":
                return api_error(
                    message="Onjuist wachtwoord.",
                    error="invalid_credentials",
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            return api_error(
                message=exc.message,
                error=exc.error,
                status=exc.status_code,
            )

        if not user.is_2fa_enabled:
            return api_error(
                message="2FA is niet actief op uw account.",
                error="not_enabled",
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not verify_user_otp(user, otp):
            return api_error(
                message="Ongeldige verificatiecode.",
                error="invalid_otp",
                status=status.HTTP_400_BAD_REQUEST,
            )

        disable_totp(user)
        return api_response(message="2FA is uitgeschakeld.")


class ResetAuthenticatorView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user, error_response = _linked_user_or_error(request)
        if error_response:
            return error_response

        disable_totp(user)
        return api_response(message="Authenticator gereset. Stel 2FA opnieuw in.")


class MfaLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = MfaLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = serializer.validated_data
        try:
            tokens = complete_mfa_login(
                data["mfa_token"],
                otp=data.get("otp"),
                backup_code=data.get("backup_code"),
            )
        except ValueError as exc:
            error_code = str(exc)
            if error_code == "invalid_token":
                return api_error(
                    message="MFA-sessie ongeldig of verlopen. Log opnieuw in.",
                    error="invalid_token",
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if error_code == "invalid_otp":
                return api_error(
                    message="Ongeldige verificatiecode.",
                    error="invalid_otp",
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            raise

        return api_response(data=tokens, message="Ingelogd.")


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @rate_limit(limit_per_minute=3)
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

    @rate_limit(limit_per_minute=5)
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return api_error(
                message=first_validation_message(serializer),
                error="validation_error",
                data=serializer.errors,
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = serializer.validated_data.get("token")
        if not token:
            return api_error(
                message="Token is vereist.",
                error="missing_token",
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


class UserDataExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user, error = _linked_user_or_error(request)
        if error:
            return error

        from django.db.models import Model
        from django.core.serializers import serialize
        from django.forms.models import model_to_dict

        export_data = {
            "exported_at": timezone.now().isoformat(),
            "user": {
                "id": str(user.id),
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email_verified": user.email_verified,
                "subscription_tier": user.subscription_tier,
                "has_fiscal_partner": user.has_fiscal_partner,
                "active_tax_year": user.active_tax_year,
                "created_at": user.created_at.isoformat(),
            },
            "portfolios": [],
            "platform_connections": [],
            "transactions": [],
        }

        from apps.portfolio.models import Portfolio, Transaction
        from apps.integrations.models import PlatformConnection

        portfolios = Portfolio.objects.filter(user=user)
        for portfolio in portfolios:
            export_data["portfolios"].append({
                "id": str(portfolio.id),
                "name": portfolio.name,
                "description": portfolio.description,
                "created_at": portfolio.created_at.isoformat(),
            })

        connections = PlatformConnection.objects.filter(user=user)
        for conn in connections:
            export_data["platform_connections"].append({
                "id": str(conn.id),
                "platform": conn.platform,
                "label": conn.label,
                "connection_method": conn.connection_method,
                "created_at": conn.created_at.isoformat(),
            })

        transactions = Transaction.objects.filter(
            position__portfolio__user=user,
        ).values(
            "id",
            "position__asset__symbol",
            "position__asset__name",
            "quantity",
            "price",
            "currency",
            "transaction_date",
        )
        export_data["transactions"] = list(transactions)

        response = Response(
            export_data,
            content_type="application/json",
        )
        response["Content-Disposition"] = f"attachment; filename=vermogenspeil-export-{user.id}.json"
        return response
