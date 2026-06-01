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
from apps.portfolio.services.dashboard import build_dashboard_summary

User = get_user_model()


class DashboardSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="dash@example.com",
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

    def test_empty_portfolio_returns_zero_total(self):
        summary = build_dashboard_summary(self.user)
        self.assertTrue(summary["has_portfolio"])
        self.assertEqual(summary["total_value_eur"], "0.00")
        self.assertEqual(summary["positions"], [])

    @patch("apps.portfolio.services.valuation.get_price_service")
    def test_cost_basis_from_transactions(self, mock_get_service):
        mock_get_service.return_value.get_live_prices.return_value = {}

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
            transaction_hash="hash-btc-1",
        )

        summary = build_dashboard_summary(self.user)

        self.assertEqual(summary["total_value_eur"], "25000.00")
        self.assertEqual(len(summary["positions"]), 1)
        self.assertEqual(summary["by_category"][0]["label"], "Crypto")
        self.assertIn("recent_activity", summary)

    def test_recent_activity_lists_latest_transactions(self):
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.btc,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.1"),
            price_eur=Decimal("50000"),
            total_eur=Decimal("5000"),
            occurred_at=timezone.now(),
            transaction_hash="hash-recent-1",
        )
        summary = build_dashboard_summary(self.user)
        self.assertEqual(len(summary["recent_activity"]), 1)
        self.assertEqual(summary["recent_activity"][0]["symbol"], "BTC")

    def test_value_history_includes_current_point(self):
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
            total_eur=Decimal("25000"),
            occurred_at=timezone.now(),
            transaction_hash="hash-history-1",
        )
        summary = build_dashboard_summary(self.user)
        history = summary["value_history"]
        self.assertGreaterEqual(len(history), 1)
        self.assertEqual(history[-1]["method"], "current")
        self.assertEqual(history[-1]["value_eur"], summary["total_value_eur"])
