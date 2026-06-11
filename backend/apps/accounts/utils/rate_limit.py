import logging
from functools import wraps

from django.core.cache import cache
from django.http import JsonResponse
from rest_framework import status

logger = logging.getLogger(__name__)


def rate_limit(limit_per_minute: int = 5):
    """
    Rate limit decorator based on client IP.
    Default: 5 requests per minute per IP.
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            client_ip = _get_client_ip(request)
            endpoint = request.path
            cache_key = f"ratelimit:{client_ip}:{endpoint}"

            current_count = cache.get(cache_key, 0)
            if current_count >= limit_per_minute:
                logger.warning(
                    f"Rate limit exceeded for IP {client_ip} on {endpoint}",
                )
                return JsonResponse(
                    {
                        "message": "Teveel aanvragen. Probeer het later opnieuw.",
                        "error": "rate_limit_exceeded",
                    },
                    status=status.HTTP_429_TOO_MANY_REQUESTS,
                )

            cache.set(cache_key, current_count + 1, timeout=60)
            return view_func(self, request, *args, **kwargs)

        return wrapper

    return decorator


def _get_client_ip(request) -> str:
    """Extract client IP from request, considering proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "unknown")
    return ip
