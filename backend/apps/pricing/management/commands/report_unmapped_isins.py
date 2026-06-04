from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.portfolio.models import Asset, AssetType
from apps.pricing.services.instrument_service import list_unmapped_isins

User = get_user_model()


class Command(BaseCommand):
    help = "Toon ISIN's zonder Yahoo-mapping"

    def add_arguments(self, parser):
        parser.add_argument("--email", default="", help="Filter op gebruiker")

    def handle(self, *args, **options):
        email = (options["email"] or "").strip().lower()
        assets = Asset.objects.exclude(asset_type=AssetType.CASH)
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if not user:
                self.stderr.write(f"Geen gebruiker: {email}")
                return
            assets = assets.filter(user=user)

        unmapped = list_unmapped_isins(list(assets.values_list("symbol", flat=True).distinct()))
        if not unmapped:
            self.stdout.write(self.style.SUCCESS("Alle ISIN's hebben een mapping."))
            return
        self.stdout.write(f"{len(unmapped)} zonder mapping:")
        for isin in sorted(unmapped):
            self.stdout.write(f"  {isin}")
