"""Development settings."""

import base64

from .base import *  # noqa: F405

DEBUG = True

SECRET_KEY = os.environ.get(  # noqa: F405
    "SECRET_KEY",
    "django-insecure-local-dev-only-change-in-production",
)

if not ENCRYPTION_KEY:  # noqa: F405
    # Moet exact 32 bytes zijn na base64-decode (AES-256)
    ENCRYPTION_KEY = base64.b64encode(b"0" * 32).decode()

if not os.environ.get("EMAIL_HOST"):  # noqa: F405
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(  # noqa: F405
    "rest_framework.renderers.BrowsableAPIRenderer",
)

# Lokale sync zonder Redis-worker — productie gebruikt Celery + Redis
CELERY_TASK_ALWAYS_EAGER = True  # noqa: F405

# Voorbeelddata / demo-koppelingen (nooit in productie)
DEMO_FEATURES_ENABLED = True  # noqa: F405

# Koers-cache lokaal zonder Redis (productie gebruikt Redis uit base.py)
CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "vermogenspeil-pricing-dev",
    }
}
