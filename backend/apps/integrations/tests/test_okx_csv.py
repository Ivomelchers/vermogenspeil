from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.csv.detection import validate_csv_for_platform
from apps.integrations.okx.import_service import import_okx_csv_for_user
from apps.integrations.okx.parser import parse_okx_csv
from apps.integrations.testing.fixtures import load_text_fixture
from apps.portfolio.models import AssetType, Transaction, TransactionType

User = get_user_model()


class OkxParserTests(TestCase):
    def test_parse_sample_fixture(self):
        content = load_text_fixture("okx", "sample-trades.csv")
        result = parse_okx_csv(content)
        self.assertEqual(len(result.rows), 3)
        self.assertEqual(result.rows[0].symbol, "BTC")
        self.assertEqual(result.rows[0].transaction_type, TransactionType.BUY)
        self.assertEqual(result.rows[1].transaction_type, TransactionType.SELL)

    def test_fingerprint_detects_okx_export(self):
        content = load_text_fixture("okx", "sample-trades.csv")
        match = validate_csv_for_platform(content, "okx")
        self.assertGreaterEqual(match.confidence, 0.85)

    def test_parse_symbol_size_price_variant_headers(self):
        content = (
            "Symbol,side,Size,Price,Fee,Time,tradeId\n"
            "BTC-EUR,buy,0.5,40000,0.02,2024-03-01 12:00:00,999\n"
        )
        row = parse_okx_csv(content).rows[0]
        self.assertEqual(row.symbol, "BTC")
        self.assertEqual(row.quantity, Decimal("0.5"))


class OkxImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="okx@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|okx-user",
        )

    def test_import_sample_fixture(self):
        content = load_text_fixture("okx", "sample-trades.csv")
        result = import_okx_csv_for_user(self.user, content)
        self.assertEqual(result["transactions_imported"], 3)
        self.assertTrue(
            Transaction.objects.filter(
                portfolio__user=self.user,
                asset__asset_type=AssetType.CRYPTO,
            ).exists()
        )
