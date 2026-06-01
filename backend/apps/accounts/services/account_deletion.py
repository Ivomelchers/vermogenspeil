"""GDPR soft-delete: account deactiveren en persoonsgegevens anonimiseren."""

import logging
import secrets

from django.db import transaction
from django.utils import timezone

from apps.accounts.models import User
from apps.integrations.models import PlatformConnection

logger = logging.getLogger(__name__)


def _try_delete_auth0_user(auth0_id: str | None) -> None:
    if not auth0_id:
        return
    try:
        from apps.accounts.authentication import get_auth0_client

        get_auth0_client().users.delete(auth0_id)
    except Exception:
        logger.warning("Auth0 verwijderen mislukt voor %s", auth0_id, exc_info=True)


@transaction.atomic
def soft_delete_user(user: User) -> None:
    """Deactiveer account, anonimiseer PII, koppel platformen los."""
    if user.deleted_at is not None:
        return

    auth0_id = user.auth_0_id
    now = timezone.now()
    token = secrets.token_hex(6)

    user.is_active = False
    user.deleted_at = now
    user.email = f"deleted-{user.pk}-{token}@deleted.invalid"
    user.first_name = ""
    user.last_name = ""
    user.auth_0_id = None
    user.email_verified = False
    user.totp_secret_encrypted = ""
    user.is_2fa_enabled = False
    user.totp_confirmed_at = None
    user.has_fiscal_partner = False
    user.save(
        update_fields=[
            "is_active",
            "deleted_at",
            "email",
            "first_name",
            "last_name",
            "auth_0_id",
            "email_verified",
            "totp_secret_encrypted",
            "is_2fa_enabled",
            "totp_confirmed_at",
            "has_fiscal_partner",
            "updated_at",
        ]
    )

    PlatformConnection.objects.filter(user=user).update(is_active=False)
    user.two_factor_backup_codes.all().delete()
    user.email_verification_tokens.filter(used_at__isnull=True).update(
        used_at=now,
    )

    transaction.on_commit(lambda: _try_delete_auth0_user(auth0_id))
