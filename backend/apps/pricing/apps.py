from django.apps import AppConfig


class PricingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.pricing"
    verbose_name = "Pricing"

    def ready(self) -> None:
        from apps.pricing.yfinance_utils import configure_yfinance_logging

        configure_yfinance_logging()
