import logging

from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.models import EmailVerificationToken, User

logger = logging.getLogger(__name__)


def build_verification_url(token: str) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/verify-email?token={token}"


def send_verification_email(user: User, verification_token: EmailVerificationToken) -> None:
    verification_url = build_verification_url(verification_token.token)
    context = {
        "user": user,
        "verification_url": verification_url,
        "valid_hours": 24,
    }
    subject = "Bevestig je e-mailadres — MijnVermogen"
    message = render_to_string("accounts/email/verify_email.txt", context)
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
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
    return user


def resend_verification_email(email: str) -> bool:
    user = User.objects.filter(email__iexact=email, email_verified=False).first()
    if user is None:
        return False

    token = EmailVerificationToken.create_for_user(user)
    send_verification_email(user, token)
    return True
