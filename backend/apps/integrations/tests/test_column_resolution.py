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

    def test_drifted_headers_fail_plain_parser(self):
        content = _read("drifted-column-headers.csv")
        with self.assertRaises(Exception):
            parse_degiro_csv(content)

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
        self.assertTrue(resolution.ai_used)
        self.assertEqual(resolution.source, "ai")

        result = parse_degiro_csv(content, column_mapping=resolution.mapped_columns)
        self.assertEqual(len(result.rows), 1)
        self.assertEqual(result.rows[0].transaction_type, "buy")

    @patch("apps.integrations.csv.column_resolution.suggest_column_mapping_with_ai")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_parse_pipeline_uses_ai_only_on_failure(self, mock_ai):
        content = _read("drifted-column-headers.csv")
        headers = content.strip().splitlines()[0].split(";")
        mock_ai.return_value = AiColumnMappingResult(
            mapped_columns=DRIFTED_AI_MAP,
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

    def test_maintenance_snippets_for_new_aliases(self):
        snippets = format_alias_maintenance_snippets(
            DEGIRO_SCHEMA,
            {"date": "Booking date now", "total": "Sum EUR"},
            source="ai",
        )
        self.assertTrue(any("booking date now" in s for s in snippets))
        self.assertTrue(any("sum eur" in s for s in snippets))

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
