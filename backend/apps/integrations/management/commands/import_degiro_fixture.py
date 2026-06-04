from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.integrations.csv.import_service import import_csv_for_user
from apps.integrations.models import PlatformType

User = get_user_model()

FIXTURE_PATH = (
    Path(__file__).resolve().parents[4] / "fixtures" / "degiro" / "sample-transactions.csv"
)


class Command(BaseCommand):
    help = "Importeer voorbeeld-DEGIRO CSV uit backend/fixtures/degiro/"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument(
            "--file",
            default=str(FIXTURE_PATH),
            help="Pad naar CSV (default: fixtures/degiro/sample-transactions.csv)",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(f"Geen gebruiker: {email}")

        path = Path(options["file"])
        if not path.exists():
            raise CommandError(f"Bestand niet gevonden: {path}")

        content = path.read_text(encoding="utf-8-sig")
        result = import_csv_for_user(
            user,
            content,
            platform=PlatformType.DEGIRO,
            label="DEGIRO (CSV fixture)",
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"DEGIRO CSV geïmporteerd: {result['transactions_imported']} nieuw, "
                f"{result['transactions_skipped']} overgeslagen."
            )
        )
