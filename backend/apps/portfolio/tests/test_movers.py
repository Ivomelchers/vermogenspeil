from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.portfolio.models import (
    Asset,
    AssetType,
    Portfolio,
    Position,
    Transaction,
    TransactionType,
    VermogensCategorie,
)
from apps.portfolio.services.movers import compute_top_movers

User = get_user_model()


class TopMoversTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="movers@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Hoofdportefeuille",
            is_default=True,
        )
        self.winner = Asset.objects.create(
            user=self.user,
            symbol="WIN",
            asset_type=AssetType.STOCK,
            category=VermogensCategorie.BELEGGING,
        )
        self.loser = Asset.objects.create(
            user=self.user,
            symbol="LOSE",
            asset_type=AssetType.STOCK,
            category=VermogensCategorie.BELEGGING,
        )
        bought_at = timezone.now() - timedelta(days=60)
        for asset, qty, price in (
            (self.winner, Decimal("1"), Decimal("100")),
            (self.loser, Decimal("1"), Decimal("100")),
        ):
            Transaction.objects.create(
                portfolio=self.portfolio,
                asset=asset,
                transaction_type=TransactionType.BUY,
                quantity=qty,
                price_eur=price,
                fee_eur=Decimal("0"),
                total_eur=qty * price,
                occurred_at=bought_at,
                transaction_hash=f"mv-{asset.symbol}",
            )
            Position.objects.create(
                portfolio=self.portfolio,
                asset=asset,
                quantity=qty,
                average_cost_eur=price,
            )

    @patch("apps.portfolio.services.movers._position_value_at_date")
    @patch("apps.portfolio.services.movers.fetch_historical_prices")
    @patch("apps.portfolio.services.movers.fetch_live_prices_for_positions")
    @patch("apps.portfolio.services.movers.position_value_eur")
    def test_losers_exclude_gainers(
        self,
        mock_position_value,
        mock_live_prices,
        mock_historical,
        mock_start_value,
    ):
        mock_live_prices.return_value = {}
        mock_historical.return_value = {}
        mock_start_value.return_value = (Decimal("100"), "historical")

        def value_side_effect(position, live_prices=None):
            if position.asset.symbol == "WIN":
                return Decimal("150"), "market"
            return Decimal("50"), "market"

        mock_position_value.side_effect = value_side_effect

        result = compute_top_movers(self.portfolio, "month", limit=3)

        self.assertEqual(len(result["gainers"]), 1)
        self.assertEqual(result["gainers"][0]["symbol"], "WIN")
        self.assertEqual(len(result["losers"]), 1)
        self.assertEqual(result["losers"][0]["symbol"], "LOSE")
        symbols = {m["symbol"] for m in result["gainers"]} & {m["symbol"] for m in result["losers"]}
        self.assertEqual(symbols, set())
