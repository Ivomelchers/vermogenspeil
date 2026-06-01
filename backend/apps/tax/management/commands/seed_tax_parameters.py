from django.core.management.base import BaseCommand

from apps.tax.services.parameters import ensure_default_parameters


class Command(BaseCommand):
    help = "Seed forfaitaire Box 3-parameters (2026)."

    def handle(self, *args, **options):
        ensure_default_parameters()
        self.stdout.write(self.style.SUCCESS("Belastingjaar-parameters bijgewerkt (2026)."))
