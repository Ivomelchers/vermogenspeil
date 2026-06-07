"""Hybride kolommapping: schema eerst, fuzzy/AI fallback."""

from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.integrations.csv.ai_column_mapping import (
    AiColumnMappingResult,
    format_alias_maintenance_snippets,
)
from apps.integrations.csv.column_resolution import resolve_column_mapping
from apps.integrations.csv.parse_pipeline import parse_csv_with_resolution
from apps.integrations.csv.registry import get_csv_parser
from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA
from apps.integrations.degiro.parser import parse_degiro_csv

FIXTURES = Path(__file__).resolve().parents[3] / "fixtures" / "degiro"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


DRIFTED_AI_MAP = {
    "date": "Booking date now",
    "time": "Hour",
    "product": "Instrument",
    "isin": "ISIN",
    "quantity": "Shares",
    "price": "Unit price",
    "fee": "Costs EUR",
    "total": "Sum EUR",
    "order_id": "Ref",
}


class ColumnResolutionTests(SimpleTestCase):
    def test_nl_export_parses_without_ai(self):
        content = _read("nl-transactions-export.csv")
        result = parse_degiro_csv(content)
        self.assertEqual(len(result.rows), 2)

    def test_drifted_headers_parse_via_schema_aliases(self):
        content = _read("drifted-column-headers.csv")
        result = parse_degiro_csv(content)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].transaction_type, "buy")

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_drifted_headers_parse_after_ai_mapping(self, mock_ai):
        content = _read("drifted-column-headers.csv")
        lines = content.strip().splitlines()
        headers = lines[0].split(";")

        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns=DRIFTED_AI_MAP,
            confidence=0.9,
            reasoning="test",
            raw_response="{}",
        )

        resolution = resolve_column_mapping(
            DEGIRO_SCHEMA,
            original_headers=headers,
            content=content,
            use_ai=True,
        )
        self.assertTrue(resolution.parser_ready)
        self.assertFalse(resolution.ai_used)
        self.assertEqual(resolution.source, "schema")
        mock_ai.assert_not_called()

        result = parse_degiro_csv(content, column_mapping=resolution.mapped_columns)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].transaction_type, "buy")

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_parse_pipeline_uses_ai_only_on_failure(self, mock_ai):
        content = (
            "Tx date;Tx time;Asset title;ID code;Seg;Floor;Qty units;Px unit;"
            "Amt loc;Val eur;Ccy pair;Conv fee;Brk fee;Net pay;Tkt\n"
            "20-02-2024;14:15:00;ASML Holding NV;NL0010273215;EAM;XAMS;2;850,00;"
            "-1700,00;-1700,00;;0,00;1,50;-1701,50;tkt-8842\n"
        )
        headers = content.strip().splitlines()[0].split(";")
        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns={
                "date": "Tx date",
                "time": "Tx time",
                "product": "Asset title",
                "isin": "ID code",
                "quantity": "Qty units",
                "price": "Px unit",
                "fee": "Brk fee",
                "total": "Net pay",
                "order_id": "Tkt",
            },
            confidence=0.9,
            reasoning="test",
            raw_response="{}",
        )

        entry = get_csv_parser("degiro")
        result, resolution = parse_csv_with_resolution(
            entry,
            content,
            original_headers=headers,
        )
        self.assertEqual(len(result.rows), 1)
        self.assertIsNotNone(resolution)
        self.assertTrue(resolution.ai_used)
        mock_ai.assert_called_once()

    def test_ai_only_fixture_parses_without_ai(self):
        content = _read("drifted-column-headers-ai-only.csv")
        result = parse_degiro_csv(content)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].transaction_type, "buy")

    def test_maintenance_snippets_for_new_aliases(self):
        snippets = format_alias_maintenance_snippets(
            DEGIRO_SCHEMA,
            {"date": "Tx date", "total": "Net pay"},
            source="ai",
        )
        self.assertTrue(any("tx date" in s for s in snippets))
        self.assertTrue(any("net pay" in s for s in snippets))

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_import_uses_preview_mapping_without_second_ai_call(self, mock_ai):
        content = (
            "Trade day;Clock time;Inst name;ISIN code;Mkt;Venue;Share qty;Unit px;"
            "Loc amt;Val EUR;FX ccy;FX fee;Fee costs;Settle total;Order ref\n"
            "15-01-2024;09:30:00;iShares Core MSCI World UCITS ETF;IE00B4L5Y983;"
            "EAM;XAMS;8;88,50;-708,00;-708,00;;0,00;2,00;-710,00;ord-1001\n"
        )
        headers = content.strip().splitlines()[0].split(";")
        mapping = {
            "date": "Trade day",
            "time": "Clock time",
            "product": "Inst name",
            "isin": "ISIN code",
            "quantity": "Share qty",
            "price": "Unit px",
            "fee": "Fee costs",
            "total": "Settle total",
            "order_id": "Order ref",
        }
        mock_ai.return_value = None

        entry = get_csv_parser("degiro")
        result, resolution = parse_csv_with_resolution(
            entry,
            content,
            original_headers=headers,
            column_mapping_override=mapping,
        )
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(resolution.source, "preview")
        mock_ai.assert_not_called()

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_drifted_headers_parse_when_ai_maps_description_to_venue(self, mock_ai):
        content = _read("drifted-column-headers.csv")
        lines = content.strip().splitlines()
        headers = lines[0].split(";")

        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns={**DRIFTED_AI_MAP, "description": "Exec venue"},
            confidence=0.9,
            reasoning="test",
            raw_response="{}",
        )

        resolution = resolve_column_mapping(
            DEGIRO_SCHEMA,
            original_headers=headers,
            content=content,
            use_ai=True,
        )
        result = parse_degiro_csv(content, column_mapping=resolution.mapped_columns)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].transaction_type, "buy")

    def test_nl_export_pipeline_no_ai_call(self):
        content = _read("nl-transactions-export.csv")
        headers = content.strip().splitlines()[0].split(";")
        entry = get_csv_parser("degiro")

        with patch(
            "apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai"
        ) as mock_ai:
            result, resolution = parse_csv_with_resolution(
                entry,
                content,
                original_headers=headers,
            )
            self.assertEqual(len(result.rows), 2)
            self.assertIsNone(resolution)
            mock_ai.assert_not_called()
