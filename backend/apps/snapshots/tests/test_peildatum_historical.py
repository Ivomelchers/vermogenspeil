from datetime import date, datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, Transaction, TransactionType, VermogensCategorie
from apps.portfolio.services.historical_valuation import portfolio_valuation_at_date
from apps.snapshots.services.peildatum import build_peildatum_payload, peildatum_date_for_year

User = get_user_model()


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
)
class PeildatumHistoricalValuationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="peil-hist@example.com",
            password="SecurePass123!",
        )
        self.portfolio = Portfolio.objects.create(user=self.user, name="Hoofd", is_default=True)
        self.asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )

    @patch("apps.portfolio.services.historical_valuation.fetch_historical_prices")
    def test_portfolio_valuation_uses_historical_price_on_peildatum(self, mock_prices):
        mock_prices.return_value = {("BTC", date(2026, 1, 1)): Decimal("48000")}
        Position.objects.create(portfolio=self.portfolio, asset=self.asset, quantity=Decimal("1"))
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("1"),
            price_eur=Decimal("40000"),
            total_eur=Decimal("40000"),
            occurred_at=datetime(2025, 6, 1, 12, 0, tzinfo=ZoneInfo("Europe/Amsterdam")),
        )

        result = portfolio_valuation_at_date(self.portfolio, date(2026, 1, 1))

        self.assertEqual(result["total_value_eur"], Decimal("48000.00"))
        self.assertEqual(result["valuation_method"], "historical_prices")
        self.assertEqual(len(result["positions"]), 1)
        self.assertEqual(result["positions"][0]["valuation_source"], "historical")

    @patch("apps.snapshots.services.peildatum.portfolio_valuation_at_date")
    def test_payload_includes_fiscale_category_in_box3_totals(self, mock_valuation):
        position = Position.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            quantity=Decimal("1"),
        )
        mock_valuation.return_value = {
            "total_value_eur": Decimal("1000"),
            "valuation_method": "historical_prices",
            "historical_priced": 1,
            "total_positions": 1,
            "positions": [
                {
                    "position": position,
                    "quantity": Decimal("1"),
                    "value_eur": Decimal("1000"),
                    "valuation_source": "historical",
                    "unit_price_eur": Decimal("1000"),
                }
            ],
        }

        payload = build_peildatum_payload(self.user, 2026)

        self.assertEqual(payload["positions"][0]["fiscale_category"], VermogensCategorie.BELEGGING)
        self.assertEqual(payload["box3_totals"]["overige_bezittingen_eur"], "1000.00")
        mock_valuation.assert_called_once_with(self.portfolio, peildatum_date_for_year(2026))
