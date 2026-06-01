from decimal import Decimal

from django.test import TestCase

from apps.tax.services.pdf_report import (
    build_box3_pdf,
    format_eur_display,
    format_generated_at,
    format_step_display,
)


class PdfReportFormattingTests(TestCase):
    def test_format_eur_display_dutch(self):
        self.assertEqual(format_eur_display("36230.16"), "€ 36.230,16")
        self.assertEqual(format_eur_display("0"), "€ 0,00")

    def test_format_step_percent(self):
        self.assertEqual(format_step_display("aandeel_percent", "81.94"), "81,94%")

    def test_format_generated_at_human(self):
        text = format_generated_at("2026-06-01T18:40:08.547526+02:00")
        self.assertIn("juni 2026", text)
        self.assertIn("18:40", text)

    def test_pdf_contains_dutch_labels(self):
        report = {
            "year": 2026,
            "generated_at": "2026-06-01T18:40:08+02:00",
            "forfaitair": {
                "available": True,
                "tax_due_eur": "0",
                "box3_inputs": {
                    "banktegoeden_eur": "0",
                    "overige_bezittingen_eur": "36230.16",
                    "schulden_eur": "0",
                },
                "calculation": {
                    "steps": {
                        "rendementsgrondslag_eur": "36230.16",
                        "grondslag_sparen_beleggen_eur": "0",
                        "belasting_netto_eur": "0",
                    },
                },
            },
            "debts": [],
            "real_estate": [],
        }
        pdf = build_box3_pdf(report)
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 800)
