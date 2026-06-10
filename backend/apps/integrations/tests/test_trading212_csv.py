from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.csv.detection import validate_csv_for_platform
from apps.integrations.models import PlatformType
from apps.integrations.testing.fixtures import load_text_fixture
from apps.integrations.trading212.import_service import import_trading212_csv_for_user
from apps.integrations.trading212.parser import parse_trading212_csv
from apps.portfolio.models import Position, Transaction, TransactionType

User = get_user_model()


class Trading212ParserTests(TestCase):
    def test_parse_sample_fixture(self):
        content = load_text_fixture("trading212", "sample-transactions.csv")
        result = parse_trading212_csv(content)
        self.assertEqual(len(result.rows), 3)
        types = {r.transaction_type for r in result.rows}
        self.assertEqual(
            types,
            {TransactionType.BUY, TransactionType.SELL, TransactionType.DIVIDEND},
        )

    def test_fingerprint_detects_trading212(self):
        content = load_text_fixture("trading212", "sample-transactions.csv")
        match = validate_csv_for_platform(content, PlatformType.TRADING212)
        self.assertGreaterEqual(match.confidence, 0.85)

    def test_buy_row_amounts(self):
        content = load_text_fixture("trading212", "sample-transactions.csv")
        buy = next(
            r for r in parse_trading212_csv(content).rows if r.transaction_type == TransactionType.BUY
        )
        self.assertEqual(buy.symbol, "IE00B4L5Y983")
        self.assertEqual(buy.quantity, Decimal("2"))
        self.assertEqual(buy.total_eur, Decimal("151.00"))
        self.assertEqual(buy.external_id, "trading212-tx-001")

    def test_skips_currency_conversion(self):
        content = (
            "Action,Time,ISIN,Ticker,Name,ID,No. of shares,Price / share,Total,Currency (Total)\n"
            "Currency conversion,2024-01-01 10:00:00,,,,cc-1,0,0,100,EUR\n"
        )
        result = parse_trading212_csv(content)
        self.assertEqual(len(result.rows), 0)
        self.assertEqual(len(result.skipped), 1)
        self.assertEqual(result.skipped[0].reason, "unknown_description")


class Trading212ImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="trading212@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_import_creates_transactions_and_positions(self):
        content = load_text_fixture("trading212", "sample-transactions.csv")
        result = import_trading212_csv_for_user(self.user, content)

        self.assertEqual(result["transactions_imported"], 3)
        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 3)
        self.assertGreater(Position.objects.filter(portfolio__user=self.user).count(), 0)

    def test_duplicate_import_skips_rows(self):
        content = load_text_fixture("trading212", "sample-transactions.csv")
        import_trading212_csv_for_user(self.user, content)
        second = import_trading212_csv_for_user(self.user, content)

        self.assertEqual(second["transactions_imported"], 0)
        self.assertEqual(second["transactions_skipped"], 3)
