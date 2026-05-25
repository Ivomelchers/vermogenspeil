"""Production settings."""

import os

from .base import *  # noqa: F403

DEBUG = False

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    raise ValueError("SECRET_KEY must be set to a secure value in production")

if not DATABASE_URL:  # noqa: F405
    raise ValueError("DATABASE_URL must be set in production")

_railway_domain = os.environ.get("RAILWAY_PUBLIC_DOMAIN")
if _railway_domain and _railway_domain not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS.append(_railway_domain)  # noqa: F405

_railway_static_url = os.environ.get("RAILWAY_STATIC_URL")
if _railway_static_url:
    host = _railway_static_url.removeprefix("https://").removeprefix("http://")
    if host and host not in ALLOWED_HOSTS:  # noqa: F405
        ALLOWED_HOSTS.append(host)  # noqa: F405

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
