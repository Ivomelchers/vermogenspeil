"""Alias voor demo seed — standaard dev-dataset voor Postman/UI."""

from django.core.management.base import BaseCommand, CommandError

from apps.integrations.management.commands.seed_demo_portfolio import Command as SeedDemoCommand


class Command(BaseCommand):
    help = "Laad volledige dev-dataset (Bitvavo + DEGIRO demo-sync). Zie ook: import_degiro_fixture."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)

    def handle(self, *args, **options):
        delegate = SeedDemoCommand()
        delegate.stdout = self.stdout
        delegate.style = self.style
        try:
            delegate.handle(email=options["email"])
        except CommandError:
            raise
        self.stdout.write(
            self.style.SUCCESS(
                "Tip: importeer DEGIRO CSV met "
                "python manage.py import_degiro_fixture --email=..."
            )
        )
