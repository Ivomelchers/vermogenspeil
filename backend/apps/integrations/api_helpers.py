"""Gedeelde API-helpers voor integrations views."""

from rest_framework import status

from apps.accounts.authentication import UnlinkedAuth0User
from apps.accounts.utils.responses import api_error


def linked_user_or_error(request):
    user = request.user
    if isinstance(user, UnlinkedAuth0User):
        return None, api_error(
            message="Account niet gekoppeld. Neem contact op met support.",
            error="account_not_linked",
            status=status.HTTP_403_FORBIDDEN,
        )
    return user, None


def require_verified_email(user):
    if not user.email_verified:
        return api_error(
            message="Bevestig eerst uw e-mailadres voordat u een platform koppelt.",
            error="email_not_verified",
            status=status.HTTP_403_FORBIDDEN,
        )
    return None
