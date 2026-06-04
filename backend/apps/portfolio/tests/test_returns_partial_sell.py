from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.integrations.degiro.import_service import import_degiro_csv_for_user
from apps.integrations.testing.fixtures import load_text_fixture
from apps.portfolio.models import AssetType, Portfolio
from apps.portfolio.services.returns import compute_return_summary
from apps.pricing.services import PriceQuote

User = get_user_model()


class ReturnSummaryPartialSellTests(TestCase):
    """Na verkoop: rendement op kostprijs open positie, niet som van alle ooit gekochte aandelen."""

    def setUp(self):
        self.user = User.objects.create_user(
            email="partial@example.com",
            password="SecurePass123!",
            first_name="Frank",
        )
        Portfolio.objects.create(user=self.user, name="Hoofd", is_default=True)

    @patch("apps.portfolio.services.valuation.get_price_service")
    def test_returns_use_open_cost_basis_after_degiro_fixture(self, mock_service):
        mock_service.return_value.get_live_prices.return_value = {
            "IE00B4L5Y983": PriceQuote(
                symbol="IE00B4L5Y983",
                asset_type=AssetType.ETF,
                price_eur=Decimal("123.88"),
                source="yahoo",
                fetched_at="2026-06-04T12:00:00+00:00",
                from_cache=False,
            ),
        }
        content = load_text_fixture("degiro", "all-transaction-types.csv")
        import_degiro_csv_for_user(self.user, content)

        portfolio = Portfolio.objects.get(user=self.user, is_default=True)
        live = mock_service.return_value.get_live_prices.return_value
        summary = compute_return_summary(portfolio, live_prices=live)

        self.assertEqual(summary["total_buy_outflow_eur"], Decimal("710.00"))
        self.assertEqual(summary["cost_basis_eur"], Decimal("532.50"))
        self.assertEqual(summary["invested_eur"], Decimal("532.50"))
        self.assertEqual(summary["current_value_eur"], Decimal("743.28"))
        self.assertEqual(summary["unrealized_return_eur"], Decimal("210.78"))
