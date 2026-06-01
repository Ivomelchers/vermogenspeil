from django.urls import path

from apps.pricing.views import LiveQuotesView

urlpatterns = [
    path("quotes/", LiveQuotesView.as_view(), name="pricing-live-quotes"),
]
