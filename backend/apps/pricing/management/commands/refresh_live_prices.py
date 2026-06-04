from django.core.management.base import BaseCommand

from apps.pricing.services.price_refresh import refresh_all_live_prices


class Command(BaseCommand):
    help = "Ververs live koerscache voor alle posities (zelfde logica als Celery-taak)."

    def handle(self, *args, **options):
        result = refresh_all_live_prices(force=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"Koersen: {result['symbols_priced']}/{result['symbols_requested']} "
                f"({result['as_of']})"
            )
        )
