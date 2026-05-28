import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class Auth0LoginError(Exception):
    def __init__(self, error: str, message: str, status_code: int = 400, data=None):
        self.error = error
        self.message = message
        self.status_code = status_code
        self.data = data or {}
        super().__init__(message)


def _token_url() -> str:
    return f"https://{settings.AUTH0_DOMAIN}/oauth/token"


def _base_payload() -> dict:
    return {
        "client_id": settings.AUTH0_FRONTEND_CLIENT_ID,
        "scope": "openid profile email offline_access",
    }


def exchange_password(email: str, password: str) -> dict:
    payload = {
        **_base_payload(),
        "grant_type": "password",
        "username": email,
        "password": password,
        "realm": settings.AUTH0_CONNECTION,
    }
    return _post_token(payload)


def exchange_refresh_token(refresh_token: str) -> dict:
    payload = {
        **_base_payload(),
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    return _post_token(payload)


def _post_token(payload: dict) -> dict:
    response = requests.post(_token_url(), json=payload, timeout=15)
    try:
        data = response.json()
    except ValueError as exc:
        logger.error("Auth0 token response is not JSON: %s", response.text)
        raise Auth0LoginError(
            "auth0_error",
            "Inloggen mislukt. Probeer het later opnieuw.",
            status_code=502,
        ) from exc

    if response.ok:
        return {
            "id_token": data["id_token"],
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", ""),
        }

    error = data.get("error", "auth0_error")
    description = data.get("error_description", "Inloggen mislukt.")

    if error in {"mfa_required", "enrollment_required"}:
        logger.warning(
            "Auth0 MFA is ingeschakeld voor %s — schakel uit in Auth0 Dashboard; "
            "Vermogenspeil gebruikt eigen TOTP.",
            payload.get("username", "unknown"),
        )
        raise Auth0LoginError(
            "auth0_mfa_conflict",
            (
                "Auth0 MFA staat nog aan. Schakel MFA uit in Auth0 Dashboard → "
                "Security → Multi-factor Auth. Vermogenspeil gebruikt eigen 2FA."
            ),
            status_code=503,
        )

    if error in {"invalid_grant", "access_denied"}:
        raise Auth0LoginError(
            "invalid_credentials",
            "Ongeldige inloggegevens.",
            status_code=401,
        )

    logger.warning("Auth0 token error: %s - %s", error, description)
    raise Auth0LoginError("auth0_error", description, status_code=400)
