import json
import logging
from urllib.parse import quote

import jwt
import requests
from auth0.authentication import GetToken
from auth0.exceptions import Auth0Error
from auth0.management import Auth0
from django.conf import settings
from django.core.exceptions import ValidationError
from rest_framework import authentication

from apps.accounts.exceptions import InvalidAuthToken, InvalidHeader, NoAuthToken
from apps.accounts.models import User

logger = logging.getLogger(__name__)

ALGORITHMS = ["RS256"]
_jwks_cache: dict | None = None


class UnlinkedAuth0User:
    """Auth0 identity without a linked Vermogenspeil user."""

    is_authenticated = False

    def __init__(self, auth0_id: str, email: str):
        self.auth_0_id = auth0_id
        self.id = auth0_id
        self.email = email


def _get_jwks():
    global _jwks_cache
    if _jwks_cache is None:
        jwks_url = f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json"
        response = requests.get(jwks_url, timeout=10)
        response.raise_for_status()
        _jwks_cache = response.json()
    return _jwks_cache


def get_token_auth_header(request):
    auth = request.headers.get("Authorization")
    if not auth:
        raise NoAuthToken()

    parts = auth.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise InvalidHeader()

    return parts[1]


def auth0_sub_from_id_token(id_token: str) -> str:
    decoded = jwt.decode(id_token, options={"verify_signature": False})
    return decoded["sub"]


def jwt_decode_token(token):
    header = jwt.get_unverified_header(token)
    public_key = None

    for jwk in _get_jwks()["keys"]:
        if jwk["kid"] == header["kid"]:
            public_key = jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk))

    if public_key is None:
        raise InvalidAuthToken("Public key not found.")

    issuer = f"https://{settings.AUTH0_DOMAIN}/"
    audience = settings.AUTH0_FRONTEND_CLIENT_ID
    return jwt.decode(
        token,
        public_key,
        issuer=issuer,
        algorithms=ALGORITHMS,
        audience=audience,
        leeway=60,
    )


def get_auth0_client():
    get_token = GetToken(
        settings.AUTH0_DOMAIN,
        settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
    )
    token = get_token.client_credentials(
        f"https://{settings.AUTH0_DOMAIN}/api/v2/",
    )
    return Auth0(settings.AUTH0_DOMAIN, token["access_token"])


def create_auth0_user(email: str, password: str) -> str:
    auth0 = get_auth0_client()
    result = auth0.users.create(
        {
            "email": email,
            "password": password,
            "email_verified": False,
            "verify_email": False,
            "connection": "Username-Password-Authentication",
        },
    )
    return result["user_id"]


def mark_auth0_email_verified(auth0_id: str) -> None:
    auth0 = get_auth0_client()
    auth0.users.update(auth0_id, {"email_verified": True})


def update_user_password(auth0_id: str, password: str) -> None:
    try:
        auth0 = get_auth0_client()
        auth0.users.update(auth0_id, {"password": password})
    except Auth0Error as err:
        raise ValidationError(str(err)) from err


def _management_api_token() -> str:
    return GetToken(
        settings.AUTH0_DOMAIN,
        settings.AUTH0_CLIENT_ID,
        client_secret=settings.AUTH0_CLIENT_SECRET,
    ).client_credentials(f"https://{settings.AUTH0_DOMAIN}/api/v2/")["access_token"]


def get_user_mfa_status(user: User) -> dict:
    if not user.auth_0_id:
        return {"enrolled": False, "status_available": True}

    token = _management_api_token()
    url = (
        f"https://{settings.AUTH0_DOMAIN}/api/v2/users/"
        f"{quote(user.auth_0_id, safe='')}/authentication-methods"
    )
    response = requests.get(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    if response.status_code == 403:
        logger.warning(
            "Auth0 MFA status forbidden for %s — voeg read:authentication_methods toe aan M2M app.",
            user.email,
        )
        return {"enrolled": False, "status_available": False}
    if not response.ok:
        logger.warning(
            "Auth0 MFA status mislukt (%s) voor %s: %s",
            response.status_code,
            user.email,
            response.text,
        )
        return {"enrolled": False, "status_available": False}

    methods = response.json()
    enrolled = any(
        method.get("type") in {"totp", "otp"} and method.get("confirmed", True)
        for method in methods
    )
    return {"enrolled": enrolled, "status_available": True}


def reset_mfa(user: User) -> None:
    token = _management_api_token()
    url = (
        f"https://{settings.AUTH0_DOMAIN}/api/v2/users/"
        f"{quote(user.auth_0_id, safe='')}/authentication-methods"
    )
    response = requests.delete(
        url,
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    response.raise_for_status()
    logger.info("Auth0 MFA gereset voor %s", user.email)


class Auth0Authentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        try:
            token = get_token_auth_header(request)
            decoded = jwt_decode_token(token)
            user = User.objects.get(auth_0_id=decoded["sub"])
        except User.DoesNotExist:
            return (
                UnlinkedAuth0User(
                    auth0_id=decoded["sub"],
                    email=decoded.get("email", ""),
                ),
                None,
            )
        except NoAuthToken:
            return None
        except Exception as exc:
            logger.debug("Auth0 token validation failed: %s", exc)
            raise InvalidAuthToken() from exc

        if not user.is_active:
            raise InvalidAuthToken("Account is gedeactiveerd.")

        return user, None
