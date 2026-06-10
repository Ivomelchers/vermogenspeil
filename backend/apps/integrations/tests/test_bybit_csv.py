from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.bybit.import_service import import_bybit_csv_for_user
from apps.integrations.bybit.parser import parse_bybit_csv
from apps.integrations.csv.detection import validate_csv_for_platform
from apps.integrations.testing.fixtures import load_text_fixture
from apps.portfolio.models import AssetType, Transaction, TransactionType

User = get_user_model()


class BybitParserTests(TestCase):
    def test_parse_sample_fixture(self):
        content = load_text_fixture("bybit", "sample-trades.csv")
        result = parse_bybit_csv(content)
        self.assertEqual(len(result.rows), 3)
        self.assertEqual(result.rows[0].symbol, "BTC")
        self.assertEqual(result.rows[0].transaction_type, TransactionType.BUY)
        self.assertEqual(result.rows[1].transaction_type, TransactionType.SELL)

    def test_fingerprint_detects_bybit_export(self):
        content = load_text_fixture("bybit", "sample-trades.csv")
        match = validate_csv_for_platform(content, "bybit")
        self.assertGreaterEqual(match.confidence, 0.85)

    def test_parse_execqty_variant_headers(self):
        content = (
            "Symbol,Side,execQty,execPrice,fee,orderId,execTime\n"
            "ETHUSDT,Buy,1,3000,0.01,ord-1,1705312200000\n"
        )
        row = parse_bybit_csv(content).rows[0]
        self.assertEqual(row.symbol, "ETH")
        self.assertEqual(row.quantity, Decimal("1"))


class BybitImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="bybit@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|bybit-user",
        )

    def test_import_sample_fixture(self):
        content = load_text_fixture("bybit", "sample-trades.csv")
        result = import_bybit_csv_for_user(self.user, content)
        self.assertEqual(result["transactions_imported"], 3)
        self.assertTrue(
            Transaction.objects.filter(
                portfolio__user=self.user,
                asset__asset_type=AssetType.CRYPTO,
            ).exists()
        )
