"""Production settings."""

import os

import dj_database_url

from .base import *  # noqa: F403

DEBUG = False
DEMO_FEATURES_ENABLED = False
CELERY_TASK_ALWAYS_EAGER = False  # noqa: F405

if not SECRET_KEY or SECRET_KEY.startswith("django-insecure"):  # noqa: F405
    raise ValueError("SECRET_KEY must be set to a secure value in production")

if not DATABASE_URL:  # noqa: F405
    raise ValueError("DATABASE_URL must be set in production")

DATABASES = {  # noqa: F405
    "default": dj_database_url.parse(
        DATABASE_URL,  # noqa: F405
        conn_max_age=600,
        ssl_require=True,
    )
}

_render_hostname = os.environ.get("RENDER_EXTERNAL_HOSTNAME")
if _render_hostname and _render_hostname not in ALLOWED_HOSTS:  # noqa: F405
    ALLOWED_HOSTS.append(_render_hostname)  # noqa: F405

_render_url = os.environ.get("RENDER_EXTERNAL_URL")
if _render_url:
    host = _render_url.removeprefix("https://").removeprefix("http://").split("/")[0]
    if host and host not in ALLOWED_HOSTS:  # noqa: F405
        ALLOWED_HOSTS.append(host)  # noqa: F405

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
