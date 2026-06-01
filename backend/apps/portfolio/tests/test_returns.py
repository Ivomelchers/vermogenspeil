from decimal import Decimal

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
from apps.portfolio.services.returns import compute_return_summary

User = get_user_model()


class ReturnSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="returns@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Hoofdportefeuille",
            is_default=True,
        )
        self.asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )

    def test_unrealized_return_on_cost_basis(self):
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("1"),
            price_eur=Decimal("40000"),
            fee_eur=Decimal("0"),
            total_eur=Decimal("40000"),
            occurred_at=timezone.now(),
            transaction_hash="ret-1",
        )
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.5"),
            price_eur=Decimal("50000"),
            fee_eur=Decimal("0"),
            total_eur=Decimal("25000"),
            occurred_at=timezone.now(),
            transaction_hash="ret-2",
        )
        Position.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            quantity=Decimal("1.5"),
        )

        summary = compute_return_summary(self.portfolio)
        self.assertEqual(summary["invested_eur"], Decimal("65000.00"))
        self.assertEqual(summary["current_value_eur"], Decimal("65000.00"))
        self.assertEqual(summary["unrealized_return_eur"], Decimal("0.00"))

    def test_dashboard_includes_returns(self):
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("1"),
            price_eur=Decimal("10000"),
            fee_eur=Decimal("0"),
            total_eur=Decimal("10000"),
            occurred_at=timezone.now(),
            transaction_hash="dash-ret",
        )
        Position.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            quantity=Decimal("1"),
        )

        dashboard = build_dashboard_summary(self.user)
        self.assertIn("returns", dashboard)
        self.assertEqual(dashboard["returns"]["invested_eur"], "10000.00")
