"""Test settings — isolated cache for test isolation."""

from .development import *  # noqa: F405

# Force all tests to use in-memory cache, isolated per test
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}
