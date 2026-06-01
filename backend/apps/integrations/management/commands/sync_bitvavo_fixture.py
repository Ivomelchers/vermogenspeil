from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.integrations.bitvavo.fixture_client import BitvavoFixtureClient
from apps.integrations.models import PlatformConnection, PlatformType, SyncJob, SyncStatus
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.services.sync import run_connection_sync
from apps.portfolio.services import get_or_create_default_portfolio

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Synchroniseer Bitvavo met JSON-fixtures (geen echte API). "
        "Gebruik voor lokaal testen zonder Bitvavo-account."
    )

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Django-user e-mailadres")
        parser.add_argument(
            "--label",
            default="Bitvavo (fixture)",
            help="Label van de platformkoppeling",
        )

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(f"Geen gebruiker gevonden: {email}")

        portfolio = get_or_create_default_portfolio(user)
        connection, created = PlatformConnection.objects.update_or_create(
            user=user,
            platform=PlatformType.BITVAVO,
            label=options["label"],
            defaults={
                "portfolio": portfolio,
                "is_active": True,
                "is_demo": False,
                "status": SyncStatus.PENDING,
            },
        )
        if created or not connection.api_key_encrypted:
            store_api_credentials(
                connection,
                api_key="fixture-key",
                api_secret="fixture-secret",
            )

        sync_job = SyncJob.objects.create(connection=connection, status=SyncStatus.PENDING)

        from apps.integrations.bitvavo import adapter as bitvavo_adapter

        original_client = bitvavo_adapter.BitvavoPlatformAdapter._client

        def _fixture_client(self):
            return BitvavoFixtureClient()

        bitvavo_adapter.BitvavoPlatformAdapter._client = _fixture_client
        try:
            run_connection_sync(sync_job.id)
        finally:
            bitvavo_adapter.BitvavoPlatformAdapter._client = original_client

        sync_job.refresh_from_db()
        connection.refresh_from_db()

        if sync_job.status != SyncStatus.SUCCESS:
            raise CommandError(sync_job.error_message or "Sync mislukt.")

        self.stdout.write(
            self.style.SUCCESS(
                f"Bitvavo fixture-sync voor {email}: "
                f"{sync_job.positions_synced} posities, "
                f"{sync_job.transactions_synced} transacties."
            )
        )
