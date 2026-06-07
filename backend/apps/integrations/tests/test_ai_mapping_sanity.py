from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.integrations.csv.ai_column_mapping import AiColumnMappingResult, suggest_column_mapping_with_ai
from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA

HEADERS = [
    "Trade day",
    "Clock time",
    "Inst name",
    "ISIN code",
    "Mkt",
    "Venue",
    "Share qty",
    "Unit px",
    "Loc amt",
    "Val EUR",
    "FX ccy",
    "FX fee",
    "Fee costs",
    "Settle total",
    "Order ref",
]

SAMPLE = [
    {
        "Trade day": "15-01-2024",
        "Clock time": "09:30:00",
        "Inst name": "iShares Core MSCI World UCITS ETF",
        "ISIN code": "IE00B4L5Y983",
        "Mkt": "EAM",
        "Venue": "XAMS",
        "Share qty": "8",
        "Unit px": "88,50",
        "Loc amt": "-708,00",
        "Val EUR": "-708,00",
        "FX ccy": "",
        "FX fee": "0,00",
        "Fee costs": "2,00",
        "Settle total": "-710,00",
        "Order ref": "ord-1001",
    }
]


class AiMappingSanityIntegrationTests(SimpleTestCase):
    @patch("apps.integrations.csv.ai_column_mapping.requests.post")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_ai_rejects_hallucinated_header_names(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"date":"Trade Day","total":"Settle total",'
                            '"quantity":"Share qty"}'
                        )
                    }
                }
            ]
        }
        mock_post.return_value.raise_for_status = lambda: None

        result = suggest_column_mapping_with_ai(
            DEGIRO_SCHEMA,
            file_headers=HEADERS,
            sample_rows=SAMPLE,
        )
        self.assertIsNotNone(result)
        self.assertNotIn("Trade Day", result.mapped_columns.values())
        self.assertEqual(result.mapped_columns["date"], "Trade day")

    @patch("apps.integrations.csv.ai_column_mapping.requests.post")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_ai_response_with_bad_description_and_val_total_is_sanitized(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"date":"Trade day","total":"Val EUR","description":"FX ccy",'
                            '"quantity":"Share qty"}'
                        )
                    }
                }
            ]
        }
        mock_post.return_value.raise_for_status = lambda: None

        result = suggest_column_mapping_with_ai(
            DEGIRO_SCHEMA,
            file_headers=HEADERS,
            sample_rows=SAMPLE,
        )
        self.assertIsNotNone(result)
        self.assertNotIn("description", result.mapped_columns)
        self.assertEqual(result.mapped_columns["total"], "Settle total")

    @patch("apps.integrations.csv.ai_column_mapping.requests.post")
    @override_settings(CSV_AI_COLUMN_MAPPING=True, OPENAI_API_KEY="test-key")
    def test_ai_response_rejected_when_date_unparseable(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": '{"date":"Mkt","total":"Settle total"}'
                    }
                }
            ]
        }
        mock_post.return_value.raise_for_status = lambda: None

        result = suggest_column_mapping_with_ai(
            DEGIRO_SCHEMA,
            file_headers=HEADERS,
            sample_rows=SAMPLE,
        )
        self.assertIsNone(result)
