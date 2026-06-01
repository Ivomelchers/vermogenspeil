from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.integrations.services.demo_seed import demo_features_enabled, seed_demo_for_user

User = get_user_model()


class Command(BaseCommand):
    help = "Vul voorbeeldportefeuille en demo-platformkoppelingen in (geen echte brokers)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--email",
            required=True,
            help="E-mailadres van de gebruiker waarvoor demo-data wordt aangemaakt.",
        )

    def handle(self, *args, **options):
        if not demo_features_enabled():
            raise CommandError(
                "Demo-functies zijn uitgeschakeld. Gebruik development settings (DEMO_FEATURES_ENABLED=True)."
            )

        email = options["email"].strip().lower()
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            raise CommandError(f"Geen gebruiker gevonden met e-mail: {email}")

        result = seed_demo_for_user(user)

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo-data geladen voor {user.email}: "
                f"portefeuille #{result['portfolio_id']}, "
                f"{len(result['connections'])} platformen, "
                f"{result['positions_synced']} posities, "
                f"{result['transactions_synced']} transacties."
            )
        )
        for conn in result["connections"]:
            self.stdout.write(f"  - {conn['label']}: {conn['status']}")
