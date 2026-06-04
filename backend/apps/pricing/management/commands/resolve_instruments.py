from django.core.management.base import BaseCommand

from apps.pricing.services.instrument_service import (
    resolve_unmapped_portfolio_isins,
    sync_seed_mappings,
)


class Command(BaseCommand):
    help = "Los ongemapte ISIN's op via OpenFIGI"

    def add_arguments(self, parser):
        parser.add_argument("--max", type=int, default=50)
        parser.add_argument("--skip-seed", action="store_true")

    def handle(self, *args, **options):
        if not options["skip_seed"]:
            sync_seed_mappings()
        report = resolve_unmapped_portfolio_isins(max_calls=options["max"])
        self.stdout.write(
            f"requested={report.requested} resolved={report.resolved} "
            f"known={report.already_known} failed={report.failed}"
        )
        for isin in report.isins_failed[:20]:
            self.stdout.write(f"  failed: {isin}")
