from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
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
from apps.portfolio.services.dashboard import build_dashboard_summary
from apps.pricing.services.price_service import PriceQuote, reset_price_service

User = get_user_model()


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }
)
class DashboardMarketValuationTests(TestCase):
    def setUp(self):
        reset_price_service()
        self.user = User.objects.create_user(
            email="market@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Hoofdportefeuille",
            is_default=True,
        )
        self.btc = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )

    def tearDown(self):
        reset_price_service()

    @patch("apps.portfolio.services.valuation.get_price_service")
    def test_dashboard_uses_market_value_when_price_available(self, mock_get_service):
        mock_service = mock_get_service.return_value
        mock_service.get_live_prices.return_value = {
            "BTC": PriceQuote(
                symbol="BTC",
                asset_type=AssetType.CRYPTO,
                price_eur=Decimal("100000"),
                source="bitvavo",
                fetched_at="2026-06-01T12:00:00+00:00",
                from_cache=False,
            ),
        }

        Position.objects.create(
            portfolio=self.portfolio,
            asset=self.btc,
            quantity=Decimal("0.5"),
        )
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.btc,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.5"),
            price_eur=Decimal("50000"),
            fee_eur=Decimal("0"),
            total_eur=Decimal("25000"),
            occurred_at=timezone.now(),
            transaction_hash="hash-btc-market",
        )

        summary = build_dashboard_summary(self.user)

        self.assertEqual(summary["valuation_method"], "market")
        self.assertEqual(summary["total_value_eur"], "50000.00")
        self.assertEqual(summary["positions"][0]["valuation_source"], "market")
        self.assertEqual(summary["positions"][0]["unit_price_eur"], "100000.00")
