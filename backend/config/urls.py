"""URL configuration for Vermogenspeil."""

from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


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
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.portfolio.urls")),
    path("api/v1/integrations/", include("apps.integrations.urls")),
    path("api/v1/pricing/", include("apps.pricing.urls")),
]
