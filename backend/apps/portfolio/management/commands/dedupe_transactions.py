from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from apps.portfolio.models import Portfolio
from apps.portfolio.services.dedupe import dedupe_portfolio_transactions

User = get_user_model()


class Command(BaseCommand):
    help = "Verwijder dubbele transacties in een portefeuille (zelfde external_id of hash)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="E-mailadres van de gebruiker")
        parser.add_argument(
            "--portfolio-id",
            type=int,
            default=None,
            help="Optioneel portefeuille-ID (standaard: alle portefeuilles van gebruiker)",
        )

    def handle(self, *args, **options):
        user = User.objects.filter(email=options["email"]).first()
        if not user:
            self.stderr.write(self.style.ERROR(f"Gebruiker niet gevonden: {options['email']}"))
            return

        portfolios = Portfolio.objects.for_user(user)
        if options["portfolio_id"]:
            portfolios = portfolios.filter(pk=options["portfolio_id"])

        if not portfolios.exists():
            self.stderr.write(self.style.ERROR("Geen portefeuille gevonden."))
            return

        for portfolio in portfolios:
            result = dedupe_portfolio_transactions(portfolio)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Portefeuille {portfolio.id}: {result['removed']} verwijderd, "
                    f"{result['remaining']} over."
                )
            )
