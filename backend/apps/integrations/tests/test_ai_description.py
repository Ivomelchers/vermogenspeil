from decimal import Decimal
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.integrations.degiro.ai_description import (
    DescriptionRowContext,
    classify_unknown_descriptions_with_ai,
)
from apps.integrations.degiro.parser import _amounts_for_row, parse_degiro_csv
from apps.portfolio.models import TransactionType


class AiDescriptionTests(SimpleTestCase):
    @patch("apps.integrations.degiro.ai_description.requests.post")
    @override_settings(CSV_AI_DESCRIPTION_CLASSIFICATION=True, OPENAI_API_KEY="test-key")
    def test_ai_classifies_unknown_description(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"Onbekende regel uit toekomstige export": "other"}'
                        )
                    }
                }
            ]
        }
        mock_post.return_value.raise_for_status = lambda: None

        ctx = DescriptionRowContext(
            description="Onbekende regel uit toekomstige export",
            quantity=Decimal("1"),
            total=Decimal("10"),
            fee=Decimal(0),
            has_product=False,
            has_isin=False,
        )
        result = classify_unknown_descriptions_with_ai([ctx])
        self.assertEqual(result[ctx.description], TransactionType.OTHER)

    @override_settings(CSV_AI_DESCRIPTION_CLASSIFICATION=False)
    def test_dividend_keeps_zero_quantity(self):
        qty, price, total = _amounts_for_row(
            TransactionType.DIVIDEND,
            quantity_raw=Decimal(0),
            price_raw=Decimal(0),
            total_raw=Decimal("-4"),
            fee_raw=Decimal(0),
        )
        self.assertEqual(qty, Decimal(0))
        self.assertIsNone(price)
        self.assertEqual(total, Decimal("4"))


class AiDescriptionParserTests(SimpleTestCase):
    @patch("apps.integrations.degiro.ai_description.requests.post")
    @override_settings(CSV_AI_DESCRIPTION_CLASSIFICATION=True, OPENAI_API_KEY="test-key")
    def test_parser_imports_unknown_row_via_ai(self, mock_post):
        mock_post.return_value.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"Onbekende regel uit toekomstige export": "other"}'
                        )
                    }
                }
            ]
        }
        mock_post.return_value.raise_for_status = lambda: None

        content = (
            "Date;Time;Product;ISIN;Description;Currency;Quantity;Price;"
            "Local value;Value;Exchange rate;Transaction costs;Total\n"
            "15-01-2024;09:30:00;iShares Core MSCI World UCITS ETF;IE00B4L5Y983;"
            "Koop;EUR;1;100,00;-100,00;-100,00;;1,00;-101,00\n"
            "16-01-2024;10:00:00;;;Onbekende regel uit toekomstige export;EUR;"
            "1;10,00;10,00;10,00;;0,00;10,00\n"
            "17-01-2024;11:00:00;iShares Core MSCI World UCITS ETF;IE00B4L5Y983;"
            "Dividend;EUR;0;0;4,00;4,00;;0,00;4,00\n"
            "18-01-2024;12:00:00;;;Degiro Fee;EUR;0;0;,-1,00;-1,00;;0,00;-1,00\n"
        )
        result = parse_degiro_csv(content)
        self.assertEqual(result.rows_recognized, 4)
        self.assertEqual(len(result.skipped), 0)
        types = {row.transaction_type for row in result.rows}
        self.assertIn(TransactionType.OTHER, types)
