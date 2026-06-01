from datetime import datetime
from zoneinfo import ZoneInfo

from django.test import TestCase

from apps.tax.services.tax_year import relevant_tax_year, tax_year_context

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


class TaxYearTests(TestCase):
    def test_before_may_first_shows_previous_year(self):
        at = datetime(2026, 4, 30, 12, 0, tzinfo=AMSTERDAM)
        self.assertEqual(relevant_tax_year(at=at), 2025)

    def test_from_may_first_shows_current_year(self):
        at = datetime(2026, 5, 2, 0, 0, tzinfo=AMSTERDAM)
        self.assertEqual(relevant_tax_year(at=at), 2026)

    def test_context_includes_rule(self):
        ctx = tax_year_context(at=datetime(2026, 6, 1, tzinfo=AMSTERDAM))
        self.assertEqual(ctx["relevant_tax_year"], 2026)
        self.assertIn("peildatum", ctx)
