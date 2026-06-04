from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.portfolio.models import TransactionType

from apps.integrations.csv.column_schema import analyze_column_schema
from apps.integrations.csv.preview import preview_csv_for_user
from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA
from apps.integrations.models import CsvImportDiagnostic, PlatformType
from apps.integrations.testing.fixtures import load_text_fixture

User = get_user_model()


class ColumnSchemaAnalysisTests(TestCase):
    def test_degiro_sample_maps_total(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        from apps.integrations.csv.headers import read_csv_headers

        normalized, _, original = read_csv_headers(content)
        analysis = analyze_column_schema(
            DEGIRO_SCHEMA,
            normalized_headers=normalized,
            original_headers=original,
        )
        self.assertIn("total", analysis.mapped_columns)
        self.assertFalse(analysis.has_blocking_issues)

    def test_subtotal_maps_to_total_canonical(self):
        content = load_text_fixture("degiro", "subtotal-instead-of-total.csv")
        from apps.integrations.csv.headers import read_csv_headers
        from apps.integrations.degiro.parser import parse_degiro_csv

        normalized, _, original = read_csv_headers(content)
        analysis = analyze_column_schema(
            DEGIRO_SCHEMA,
            normalized_headers=normalized,
            original_headers=original,
        )
        self.assertEqual(analysis.mapped_columns.get("total"), "Subtotal")
        result = parse_degiro_csv(content)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].total_eur, Decimal("101.00"))

    def test_nl_export_waarde_eur_not_listed_as_unmapped(self):
        content = load_text_fixture("degiro", "nl-transactions-export.csv")
        from apps.integrations.csv.headers import read_csv_headers

        normalized, _, original = read_csv_headers(content)
        analysis = analyze_column_schema(
            DEGIRO_SCHEMA,
            normalized_headers=normalized,
            original_headers=original,
        )
        self.assertEqual(analysis.mapped_columns.get("total"), "Totaal EUR")
        self.assertNotIn("Waarde EUR", analysis.unmapped_headers)
        codes = {w["code"] for w in analysis.schema_warnings}
        self.assertIn("column_by_design", codes)

    def test_buy_negative_total_in_official_export_is_positive(self):
        content = load_text_fixture("degiro", "sample-transactions.csv")
        from apps.integrations.degiro.parser import parse_degiro_csv

        row = parse_degiro_csv(content).rows[0]
        self.assertEqual(row.transaction_type, TransactionType.BUY)
        self.assertGreater(row.total_eur, 0)


class ColumnSchemaPreviewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="schema@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_preview_records_diagnostic_with_schema(self):
        content = load_text_fixture("degiro", "subtotal-instead-of-total.csv")
        result = preview_csv_for_user(self.user, content, platform=PlatformType.DEGIRO)
        self.assertEqual(result["summary"]["new"], 1)
        self.assertEqual(CsvImportDiagnostic.objects.filter(user=self.user).count(), 1)
