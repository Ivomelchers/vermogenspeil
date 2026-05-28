"""Development settings."""

import base64

from .base import *  # noqa: F405

DEBUG = True

SECRET_KEY = os.environ.get(  # noqa: F405
    "SECRET_KEY",
    "django-insecure-local-dev-only-change-in-production",
)

if not ENCRYPTION_KEY:  # noqa: F405
    ENCRYPTION_KEY = base64.b64encode(b"dev-only-32-byte-key-change!!").decode()

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(  # noqa: F405
    "rest_framework.renderers.BrowsableAPIRenderer",
)
