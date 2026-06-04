from django.core.management.base import BaseCommand

from apps.pricing.models import InstrumentMapping
from apps.pricing.services.instrument_service import sync_seed_mappings


class Command(BaseCommand):
    help = "Synchroniseer euronext_isin_tickers.json naar InstrumentMapping (DB)"

    def handle(self, *args, **options):
        created, updated = sync_seed_mappings()
        total = InstrumentMapping.objects.count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Seed gesynchroniseerd ({created} nieuw, {updated} bijgewerkt). "
                f"Totaal in DB: {total}."
            )
        )
