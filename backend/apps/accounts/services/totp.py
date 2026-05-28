import hashlib
import json
import secrets
from datetime import timedelta

import pyotp
from django.utils import timezone

from apps.accounts.models import MfaLoginChallenge, TwoFactorBackupCode, User
from apps.accounts.utils.encryption import decrypt_value, encrypt_value

MFA_CHALLENGE_VALIDITY = timedelta(minutes=5)
BACKUP_CODE_COUNT = 8
TOTP_ISSUER = "Vermogenspeil"


def _totp_for_user(user: User) -> pyotp.TOTP:
    secret = decrypt_value(user.totp_secret_encrypted)
    return pyotp.TOTP(secret)


def get_user_2fa_status(user: User) -> dict:
    return {"enrolled": user.is_2fa_enabled, "status_available": True}


def start_totp_setup(user: User) -> dict:
    if user.is_2fa_enabled:
        raise ValueError("already_enabled")

    secret = pyotp.random_base32()
    user.totp_secret_encrypted = encrypt_value(secret)
    user.totp_confirmed_at = None
    user.save(update_fields=["totp_secret_encrypted", "totp_confirmed_at"])

    totp = pyotp.TOTP(secret)
    return {
        "secret": secret,
        "barcode_uri": totp.provisioning_uri(name=user.email, issuer_name=TOTP_ISSUER),
    }


def confirm_totp_setup(user: User, otp: str) -> list[str]:
    if user.is_2fa_enabled:
        raise ValueError("already_enabled")
    if not user.totp_secret_encrypted:
        raise ValueError("setup_not_started")

    totp = _totp_for_user(user)
    if not totp.verify(otp, valid_window=1):
        raise ValueError("invalid_otp")

    user.is_2fa_enabled = True
    user.totp_confirmed_at = timezone.now()
    user.save(update_fields=["is_2fa_enabled", "totp_confirmed_at"])
    return _generate_backup_codes(user)


def verify_user_otp(user: User, otp: str) -> bool:
    if not user.totp_secret_encrypted:
        return False
    return _totp_for_user(user).verify(otp, valid_window=1)


def disable_totp(user: User) -> None:
    user.is_2fa_enabled = False
    user.totp_secret_encrypted = ""
    user.totp_confirmed_at = None
    user.save(update_fields=["is_2fa_enabled", "totp_secret_encrypted", "totp_confirmed_at"])
    TwoFactorBackupCode.objects.filter(user=user).delete()


def create_mfa_login_challenge(user: User, tokens: dict) -> MfaLoginChallenge:
    MfaLoginChallenge.objects.filter(user=user, used_at__isnull=True).update(
        used_at=timezone.now(),
    )
    return MfaLoginChallenge.objects.create(
        user=user,
        token=secrets.token_urlsafe(32),
        tokens_encrypted=encrypt_value(json.dumps(tokens)),
        expires_at=timezone.now() + MFA_CHALLENGE_VALIDITY,
    )


def complete_mfa_login(
    mfa_token: str,
    *,
    otp: str | None = None,
    backup_code: str | None = None,
) -> dict:
    challenge = (
        MfaLoginChallenge.objects.select_related("user")
        .filter(token=mfa_token)
        .first()
    )
    if challenge is None or not challenge.is_valid():
        raise ValueError("invalid_token")

    user = challenge.user
    verified = False
    if otp:
        if user.totp_secret_encrypted:
            verified = _totp_for_user(user).verify(otp, valid_window=1)
    elif backup_code:
        verified = _use_backup_code(user, backup_code)

    if not verified:
        raise ValueError("invalid_otp")

    tokens = json.loads(decrypt_value(challenge.tokens_encrypted))
    challenge.mark_used()
    return tokens


def _generate_backup_codes(user: User) -> list[str]:
    TwoFactorBackupCode.objects.filter(user=user).delete()
    codes = []
    for _ in range(BACKUP_CODE_COUNT):
        plain = secrets.token_hex(4).upper()
        TwoFactorBackupCode.objects.create(
            user=user,
            code_hash=hashlib.sha256(plain.encode()).hexdigest(),
        )
        codes.append(plain)
    return codes


def _use_backup_code(user: User, code: str) -> bool:
    normalized = code.strip().upper().replace("-", "")
    code_hash = hashlib.sha256(normalized.encode()).hexdigest()
    backup = TwoFactorBackupCode.objects.filter(
        user=user,
        code_hash=code_hash,
        used_at__isnull=True,
    ).first()
    if backup is None:
        return False

    backup.used_at = timezone.now()
    backup.save(update_fields=["used_at"])
    return True
