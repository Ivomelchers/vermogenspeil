from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.degiro.parser import parse_degiro_csv
from apps.integrations.testing.fixtures import load_text_fixture
from apps.portfolio.models import Portfolio, Transaction, TransactionType
from apps.portfolio.services.dashboard import build_dashboard_summary
from apps.portfolio.services.transaction_amounts import (
    buy_cash_outflow_eur,
    transaction_buy_cash_outflow,
)
from apps.pricing.instrument_resolver import resolve_yahoo_ticker

User = get_user_model()


class TransactionAmountsTests(TestCase):
    def test_buy_cash_outflow_prefers_total_eur(self):
        self.assertEqual(
            buy_cash_outflow_eur(
                quantity=Decimal("8"),
                price_eur=None,
                fee_eur=Decimal("2"),
                total_eur=Decimal("710"),
            ),
            Decimal("710"),
        )

    def test_nl_degiro_parse_sets_unit_price(self):
        content = load_text_fixture("degiro", "nl-transactions-export.csv")
        row = parse_degiro_csv(content).rows[0]
        self.assertEqual(row.transaction_type, TransactionType.BUY)
        self.assertIsNotNone(row.price_eur)
        self.assertGreater(row.price_eur, Decimal("0"))

    def test_isin_maps_to_yahoo_ticker(self):
        self.assertEqual(resolve_yahoo_ticker("IE00B4L5Y983"), "IWDA.AS")


class DashboardInvestedAfterImportTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="invested@example.com",
            password="SecurePass123!",
            first_name="Ivo",
        )
        Portfolio.objects.create(user=self.user, name="Hoofd", is_default=True)

    @patch("apps.portfolio.services.valuation.get_price_service")
    def test_invested_reflects_degiro_totals_not_only_fees(self, mock_service):
        mock_service.return_value.get_live_prices.return_value = {}
        content = load_text_fixture("degiro", "nl-transactions-export.csv")
        import_degiro_csv_for_user(self.user, content)

        summary = build_dashboard_summary(self.user)
        invested = Decimal(summary["returns"]["invested_eur"])
        self.assertGreater(invested, Decimal("100"))

        buys = Transaction.objects.filter(
            portfolio__user=self.user,
            transaction_type=TransactionType.BUY,
        )
        manual_sum = sum(transaction_buy_cash_outflow(tx) for tx in buys)
        self.assertEqual(invested, manual_sum.quantize(Decimal("0.01")))
