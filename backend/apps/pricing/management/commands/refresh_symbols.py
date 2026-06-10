"""
Management command to refresh symbol cache from price providers.

Usage:
    python manage.py refresh_symbols
    python manage.py refresh_symbols --force  # Ignore existing cache
"""

import logging
from django.core.management.base import BaseCommand

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Refresh symbol cache from price providers (Bitvavo, CoinGecko, etc.)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force refresh even if cache is fresh",
        )

    def handle(self, *args, **options):
        from apps.pricing.services.symbol_discovery import get_symbol_discovery_service

        self.stdout.write("Refreshing symbol cache...")

        service = get_symbol_discovery_service()
        results = service.refresh_all()

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully refreshed symbols:\n"
                f"  - Crypto: {results['crypto_total']} symbols\n"
                f"  - Stocks: {results['stocks_total']} symbols"
            )
        )
