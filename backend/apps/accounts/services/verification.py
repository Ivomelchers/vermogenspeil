import logging

from django.conf import settings
from django.utils import timezone

from apps.accounts.models import EmailLog, EmailVerificationToken, User
from apps.accounts.services.email_service import send_email

logger = logging.getLogger(__name__)


def send_verification_email(user: User, verification_token: EmailVerificationToken) -> None:
    verification_link = f"{settings.FRONTEND_URL}/verify-email?token={verification_token.token}"
    send_email(
        user=user,
        email_type=EmailLog.EmailType.VERIFICATION,
        subject="Verify your email — Vermogenspeil",
        recipient=user.email,
        template_data={"verification_link": verification_link}
    )
    logger.info("Verificatie-e-mail verstuurd naar %s", user.email)


def verify_email_token(token: str) -> User:
    verification_token = (
        EmailVerificationToken.objects.select_related("user")
        .filter(token=token, used_at__isnull=True)
        .first()
    )
    if verification_token is None:
        raise ValueError("invalid_token")
    if not verification_token.is_valid():
        raise ValueError("expired_token")

    user = verification_token.user
    user.email_verified = True
    user.email_verified_at = timezone.now()
    user.save(update_fields=["email_verified", "email_verified_at"])
    verification_token.mark_used()

    if user.auth_0_id:
        from apps.accounts.authentication import mark_auth0_email_verified

        mark_auth0_email_verified(user.auth_0_id)

    return user


def resend_verification_email(email: str) -> bool:
    user = User.objects.filter(email__iexact=email, email_verified=False).first()
    if user is None:
        return False

    token = EmailVerificationToken.create_for_user(user)
    send_verification_email(user, token)
    return True
