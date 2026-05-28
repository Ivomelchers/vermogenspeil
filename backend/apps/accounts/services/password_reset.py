import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from apps.accounts.authentication import update_user_password
from apps.accounts.models import PasswordResetToken
from apps.accounts.security import generate_hashed_secure_token

logger = logging.getLogger(__name__)
User = get_user_model()


def build_password_reset_url(plain_token: str) -> str:
    frontend_url = settings.FRONTEND_URL.rstrip("/")
    return f"{frontend_url}/#/auth/password/reset?token={plain_token}"


def send_password_reset_email(user: User, plain_token: str) -> None:
    reset_url = build_password_reset_url(plain_token)
    context = {
        "user": user,
        "reset_url": reset_url,
        "valid_hours": settings.PASSWORD_RESET_TOKEN_HOURS,
    }
    subject = "Wachtwoord resetten — MijnVermogen"
    message = render_to_string("accounts/email/password_reset.txt", context)
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    logger.info("Wachtwoord-reset e-mail verstuurd naar %s", user.email)


def request_password_reset(email: str) -> None:
    user = User.objects.filter(email__iexact=email, is_active=True).first()
    if user is None or not user.auth_0_id:
        return

    plain_token, hashed_token = generate_hashed_secure_token()
    PasswordResetToken.objects.create(user=user, token=hashed_token)
    send_password_reset_email(user, plain_token)


def _get_valid_reset_token(plain_token: str) -> PasswordResetToken:
    import hashlib

    hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
    reset_token = (
        PasswordResetToken.objects.select_related("user")
        .filter(token=hashed_token, used=False)
        .first()
    )
    if reset_token is None:
        raise ValueError("invalid_token")

    expiry = reset_token.created_at + timezone.timedelta(
        hours=settings.PASSWORD_RESET_TOKEN_HOURS,
    )
    if timezone.now() >= expiry:
        raise ValueError("expired_token")

    return reset_token


def validate_password_reset_token(plain_token: str) -> User:
    return _get_valid_reset_token(plain_token).user


def reset_password(plain_token: str, password: str) -> User:
    reset_token = _get_valid_reset_token(plain_token)
    user = reset_token.user
    update_user_password(user.auth_0_id, password)

    PasswordResetToken.objects.filter(user=user, used=False).update(used=True)
    logger.info("Wachtwoord gereset voor %s via Auth0", user.email)
    return user
