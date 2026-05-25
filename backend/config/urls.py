"""URL configuration for Vermogenspeil."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import path


def health_check(_request):
    return JsonResponse(
        {
            "data": {"status": "ok"},
            "error": None,
            "message": "Vermogenspeil API is running",
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/health/", health_check, name="health-check"),
]
