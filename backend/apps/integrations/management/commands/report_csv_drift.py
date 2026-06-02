from collections import Counter
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.integrations.models import CsvImportDiagnostic

User = get_user_model()


class Command(BaseCommand):
    help = "Overzicht CSV schema-drift (onbekende kolommen/omschrijvingen) voor onderhoud."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30, help="Aantal dagen terug")
        parser.add_argument("--platform", type=str, default="", help="Filter op platform")

    def handle(self, *args, **options):
        since = timezone.now() - timedelta(days=options["days"])
        qs = CsvImportDiagnostic.objects.filter(created_at__gte=since)
        if options["platform"]:
            qs = qs.filter(platform=options["platform"])

        if not qs.exists():
            self.stdout.write(self.style.WARNING("Geen CSV-diagnostiek in deze periode."))
            return

        self.stdout.write(f"CSV drift rapport (sinds {since.date()}, {qs.count()} events)\n")

        by_platform = qs.values_list("platform", flat=True).distinct()
        for platform in sorted(by_platform):
            platform_qs = qs.filter(platform=platform)
            self.stdout.write(self.style.MIGRATE_HEADING(f"\n{platform}"))

            unmapped = Counter()
            unknown = Counter()
            suggestions = Counter()
            for row in platform_qs:
                for header in row.unmapped_headers or []:
                    unmapped[header] += 1
                for desc in row.unknown_descriptions or []:
                    unknown[desc] += 1
                for item in row.suggested_aliases or []:
                    key = f"{item.get('file_header')} → {item.get('canonical')}"
                    suggestions[key] += 1

            if unmapped:
                self.stdout.write("  Ongebruikte kolommen:")
                for name, count in unmapped.most_common(15):
                    self.stdout.write(f"    {count:4d}×  {name}")

            if suggestions:
                self.stdout.write("  Voorgestelde alias-koppelingen (nog niet actief):")
                for name, count in suggestions.most_common(15):
                    self.stdout.write(f"    {count:4d}×  {name}")

            if unknown:
                self.stdout.write("  Onbekende omschrijvingen:")
                for name, count in unknown.most_common(15):
                    self.stdout.write(f"    {count:4d}×  {name}")

            warnings = Counter()
            for row in platform_qs:
                for warn in row.schema_warnings or []:
                    if warn.get("severity") == "warning":
                        warnings[warn.get("code", "?")] += 1
            if warnings:
                self.stdout.write("  Schema-waarschuwingen:")
                for code, count in warnings.most_common():
                    self.stdout.write(f"    {count:4d}×  {code}")

        self.stdout.write(self.style.SUCCESS("\nKlaar. Voeg aliases toe in column_schema per platform."))
