from decimal import Decimal

from django.test import TestCase

from apps.tax.services.forfaitair import ForfaitairParams, calculate_forfaitair
from apps.tax.services.parameters import ensure_default_parameters
from apps.tax.services.snapshot_inputs import extract_box3_totals_from_snapshot_data


class ForfaitairCalculatorTests(TestCase):
    def test_official_belastingdienst_example_2026(self):
        """Ivo-doc / BD-rekenvoorbeeld: B=150k, O=275k, S=100k → €4.667."""
        params = ForfaitairParams(
            pb=Decimal("0.0128"),
            po=Decimal("0.06"),
            ps=Decimal("0.027"),
            tarief=Decimal("0.36"),
            heffingsvrij=Decimal("59357"),
            schuldendrempel=Decimal("3800"),
        )
        result = calculate_forfaitair(
            banktegoeden=Decimal(150_000),
            overige_bezittingen=Decimal(275_000),
            schulden=Decimal(100_000),
            params=params,
        )
        self.assertEqual(result.belasting_netto, Decimal("4667"))
        self.assertEqual(result.aandeel_percent, Decimal("81.94"))

    def test_zero_grondslag_no_tax(self):
        params = ForfaitairParams(
            pb=Decimal("0.0128"),
            po=Decimal("0.06"),
            ps=Decimal("0.027"),
            tarief=Decimal("0.36"),
            heffingsvrij=Decimal("59357"),
            schuldendrempel=Decimal("3800"),
        )
        result = calculate_forfaitair(
            banktegoeden=Decimal(1000),
            overige_bezittingen=Decimal(0),
            schulden=Decimal(0),
            params=params,
        )
        self.assertEqual(result.belasting_netto, Decimal(0))

    def test_fiscal_partner_doubles_thresholds(self):
        params = ForfaitairParams(
            pb=Decimal("0.0128"),
            po=Decimal("0.06"),
            ps=Decimal("0.027"),
            tarief=Decimal("0.36"),
            heffingsvrij=Decimal("59357"),
            schuldendrempel=Decimal("3800"),
        )
        solo = calculate_forfaitair(
            banktegoeden=Decimal(200_000),
            overige_bezittingen=Decimal(0),
            schulden=Decimal(0),
            params=params,
            has_fiscal_partner=False,
        )
        partner = calculate_forfaitair(
            banktegoeden=Decimal(200_000),
            overige_bezittingen=Decimal(0),
            schulden=Decimal(0),
            params=params,
            has_fiscal_partner=True,
        )
        self.assertLess(partner.belasting_netto, solo.belasting_netto)

    def test_seed_2026_parameters(self):
        ensure_default_parameters()
        from apps.tax.models import TaxYearParameter

        row = TaxYearParameter.objects.get(year=2026)
        self.assertEqual(row.heffingsvrij_vermogen, Decimal("59357.00"))

    def test_snapshot_box3_totals_from_positions(self):
        data = {
            "positions": [
                {"value_eur": "1000.00", "fiscale_category": "banktegoed"},
                {"value_eur": "5000.00", "fiscale_category": "belegging"},
                {"value_eur": "2000.00", "fiscale_category": "schuld"},
            ]
        }
        totals = extract_box3_totals_from_snapshot_data(data)
        self.assertEqual(totals["banktegoeden_eur"], "1000.00")
        self.assertEqual(totals["overige_bezittingen_eur"], "5000.00")
        self.assertEqual(totals["schulden_eur"], "2000.00")
