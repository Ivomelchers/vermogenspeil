"""Development settings."""

from .base import *  # noqa: F403

DEBUG = True

SECRET_KEY = os.environ.get(  # noqa: F405
    "SECRET_KEY",
    "django-insecure-local-dev-only-change-in-production",
)

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"].append(  # noqa: F405
    "rest_framework.renderers.BrowsableAPIRenderer",
)
