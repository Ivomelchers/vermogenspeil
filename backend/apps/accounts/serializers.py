from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils import timezone
from rest_framework import serializers

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
        user = User.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            terms_accepted_at=timezone.now(),
            email_verified=False,
        )
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


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
