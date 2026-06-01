from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

from apps.accounts.authentication import create_auth0_user
from apps.accounts.models import EmailVerificationToken
from apps.accounts.services.verification import send_verification_email

User = get_user_model()


class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=12)
    first_name = serializers.CharField(max_length=150)
    terms_accepted = serializers.BooleanField()

    def validate_email(self, value):
        normalized = value.lower().strip()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError("Dit e-mailadres is al geregistreerd.")
        return normalized

    def validate_terms_accepted(self, value):
        if not value:
            raise serializers.ValidationError(
                "Je moet akkoord gaan met de algemene voorwaarden.",
            )
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value

    def create(self, validated_data):
        validated_data.pop("terms_accepted")
        email = validated_data["email"]
        password = validated_data.pop("password")

        auth0_id = create_auth0_user(email, password)
        user = User.objects.create_user(
            email=email,
            password=None,
            auth_0_id=auth0_id,
            first_name=validated_data["first_name"],
            terms_accepted_at=timezone.now(),
            email_verified=False,
        )
        user.set_unusable_password()

        token = EmailVerificationToken.create_for_user(user)
        send_verification_email(user, token)
        return user


class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField(max_length=64)


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate_email(self, value):
        return value.lower().strip()


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class TwoFactorVerifySerializer(serializers.Serializer):
    otp = serializers.CharField(max_length=10)


class TwoFactorDisableSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)
    otp = serializers.CharField(max_length=10)


class MfaLoginSerializer(serializers.Serializer):
    mfa_token = serializers.CharField(max_length=64)
    otp = serializers.CharField(max_length=10, required=False, allow_blank=True)
    backup_code = serializers.CharField(max_length=32, required=False, allow_blank=True)

    def validate(self, attrs):
        otp = (attrs.get("otp") or "").strip()
        backup_code = (attrs.get("backup_code") or "").strip()
        if not otp and not backup_code:
            raise serializers.ValidationError(
                "Voer een verificatiecode of backupcode in.",
            )
        attrs["otp"] = otp or None
        attrs["backup_code"] = backup_code or None
        return attrs


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=12)

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as exc:
            raise serializers.ValidationError(list(exc.messages)) from exc
        return value


class UserSerializer(serializers.ModelSerializer):
    is_premium = serializers.BooleanField(read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "email_verified",
            "subscription_tier",
            "is_premium",
            "active_tax_year",
            "has_fiscal_partner",
            "is_2fa_enabled",
        ]
        read_only_fields = fields


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["has_fiscal_partner"]
