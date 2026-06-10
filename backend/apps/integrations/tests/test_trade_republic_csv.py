from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.csv.detection import validate_csv_for_platform
from apps.integrations.models import PlatformType
from apps.integrations.testing.fixtures import load_text_fixture
from apps.integrations.trade_republic.import_service import import_trade_republic_csv_for_user
from apps.integrations.trade_republic.parser import parse_trade_republic_csv
from apps.portfolio.models import AssetType, Position, Transaction, TransactionType

User = get_user_model()


class TradeRepublicParserTests(TestCase):
    def test_parse_sample_fixture(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        result = parse_trade_republic_csv(content)
        self.assertEqual(len(result.rows), 4)
        types = {r.transaction_type for r in result.rows}
        self.assertEqual(
            types,
            {
                TransactionType.BUY,
                TransactionType.SELL,
                TransactionType.DIVIDEND,
                TransactionType.DEPOSIT,
            },
        )

    def test_fingerprint_detects_trade_republic(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        match = validate_csv_for_platform(content, PlatformType.TRADE_REPUBLIC)
        self.assertGreaterEqual(match.confidence, 0.85)

    def test_sale_uses_negative_shares(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        sale = next(
            r
            for r in parse_trade_republic_csv(content).rows
            if r.transaction_type == TransactionType.SELL
        )
        self.assertEqual(sale.symbol, "US6701002056")
        self.assertEqual(sale.quantity, Decimal("5"))
        self.assertEqual(sale.total_eur, Decimal("482.99"))
        self.assertEqual(sale.fee_eur, Decimal("1"))

    def test_purchase_includes_commission_in_fee(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        buy = next(
            r
            for r in parse_trade_republic_csv(content).rows
            if r.transaction_type == TransactionType.BUY
        )
        self.assertEqual(buy.total_eur, Decimal("136.14"))
        self.assertEqual(buy.fee_eur, Decimal("1"))
        self.assertEqual(buy.price_eur, Decimal("135.14"))


class TradeRepublicImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="trade-republic@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_import_creates_transactions_and_positions(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        result = import_trade_republic_csv_for_user(self.user, content)

        self.assertEqual(result["transactions_imported"], 4)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 4)
        self.assertGreater(Position.objects.filter(portfolio__user=self.user).count(), 0)

    def test_import_includes_cash_position(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        import_trade_republic_csv_for_user(self.user, content)

        cash_positions = Position.objects.filter(
            portfolio__user=self.user,
            asset__asset_type=AssetType.CASH,
        )
        self.assertTrue(cash_positions.exists())

    def test_duplicate_import_skips_rows(self):
        content = load_text_fixture("trade_republic", "sample-transactions.csv")
        import_trade_republic_csv_for_user(self.user, content)
        second = import_trade_republic_csv_for_user(self.user, content)

        self.assertEqual(second["transactions_imported"], 0)
        self.assertEqual(second["transactions_skipped"], 4)
