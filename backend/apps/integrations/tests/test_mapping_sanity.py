from django.test import SimpleTestCase

from apps.integrations.csv.mapping_sanity import (
    is_weak_total_header,
    prefer_settlement_total_mapping,
    sanitize_mapped_columns,
    validate_mapping_against_samples,
)

SAMPLE_ROW = {
    "Trade day": "15-01-2024",
    "Clock time": "09:30:00",
    "Inst name": "iShares Core MSCI World UCITS ETF",
    "ISIN code": "IE00B4L5Y983",
    "Share qty": "8",
    "Unit px": "88,50",
    "Loc amt": "-708,00",
    "Val EUR": "-708,00",
    "Fee costs": "2,00",
    "Settle total": "-710,00",
    "Order ref": "ord-1001",
    "FX ccy": "",
}

HEADERS = list(SAMPLE_ROW.keys())


class MappingSanityTests(SimpleTestCase):
    def test_sanitize_removes_fx_ccy_description(self):
        mapped = sanitize_mapped_columns(
            {
                "date": "Trade day",
                "total": "Settle total",
                "description": "FX ccy",
            },
            original_headers=HEADERS,
        )
        self.assertNotIn("description", mapped)
        self.assertEqual(mapped["total"], "Settle total")

    def test_prefer_settlement_over_val_eur(self):
        mapped = prefer_settlement_total_mapping(
            {"date": "Trade day", "total": "Val EUR"},
            HEADERS,
        )
        self.assertEqual(mapped["total"], "Settle total")

    def test_validate_auto_fixes_val_eur_to_settle_total(self):
        result = validate_mapping_against_samples(
            {"date": "Trade day", "total": "Val EUR"},
            [SAMPLE_ROW],
            original_headers=HEADERS,
        )
        self.assertTrue(result.ok)
        self.assertEqual(result.mapped_columns["total"], "Settle total")

    def test_validate_accepts_settle_total(self):
        result = validate_mapping_against_samples(
            {
                "date": "Trade day",
                "time": "Clock time",
                "total": "Settle total",
                "quantity": "Share qty",
            },
            [SAMPLE_ROW],
            original_headers=HEADERS,
        )
        self.assertTrue(result.ok)

    def test_is_weak_total_header(self):
        self.assertTrue(is_weak_total_header("Val EUR"))
        self.assertFalse(is_weak_total_header("Settle total"))
