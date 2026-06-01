from decimal import Decimal

from django.test import TestCase

from apps.tax.services.forfaitair import ForfaitairParams
from apps.tax.services.werkelijk import calculate_werkelijk


class WerkelijkCalculatorTests(TestCase):
    def test_official_example_chapter_12(self):
        """Ivo-doc: WR = €2.860, belasting = round(2860 × 0.36) = €1.030."""
        params = ForfaitairParams(
            pb=Decimal("0.0128"),
            po=Decimal("0.06"),
            ps=Decimal("0.027"),
            tarief=Decimal("0.36"),
            heffingsvrij=Decimal("59357"),
            schuldendrempel=Decimal("3800"),
        )
        aggregates = {
            "dividend": Decimal("600"),
            "rente_bank": Decimal("500"),
            "huur": Decimal(0),
            "staking": Decimal(0),
            "overige_inkomsten": Decimal(0),
            "netto_inleg": Decimal("5000"),
            "rente_schulden": Decimal("540"),
        }
        result = calculate_werkelijk(
            w_start=Decimal("90000"),
            w_end=Decimal("97300"),
            aggregates=aggregates,
            params=params,
        )
        self.assertEqual(result.werkelijk_rendement, Decimal("2860"))
        self.assertEqual(result.belasting, Decimal("1030"))

    def test_negative_werkelijk_yields_zero_tax(self):
        params = ForfaitairParams(
            pb=Decimal("0.0128"),
            po=Decimal("0.06"),
            ps=Decimal("0.027"),
            tarief=Decimal("0.36"),
            heffingsvrij=Decimal("59357"),
            schuldendrempel=Decimal("3800"),
        )
        result = calculate_werkelijk(
            w_start=Decimal("100000"),
            w_end=Decimal("50000"),
            aggregates={
                "dividend": Decimal(0),
                "rente_bank": Decimal(0),
                "huur": Decimal(0),
                "staking": Decimal(0),
                "overige_inkomsten": Decimal(0),
                "netto_inleg": Decimal(0),
            },
            params=params,
        )
        self.assertEqual(result.werkelijk_belastbaar, Decimal(0))
        self.assertEqual(result.belasting, Decimal(0))
