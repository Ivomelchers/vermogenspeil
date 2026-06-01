from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, VermogensCategorie
from apps.portfolio.services import get_or_create_default_portfolio
from apps.snapshots.services.peildatum import create_peildatum_snapshot
from apps.tax.services.box3 import build_forfaitair_summary
from apps.tax.services.parameters import ensure_default_parameters

User = get_user_model()


class ForfaitairBox3SummaryTests(TestCase):
    def setUp(self):
        ensure_default_parameters()
        self.user = User.objects.create_user(
            email="tax-api@example.com",
            password="SecurePass123!",
        )
        self.portfolio = get_or_create_default_portfolio(self.user)
        self.asset = Asset.objects.create(
            user=self.user,
            symbol="IWDA",
            name="IWDA",
            asset_type=AssetType.ETF,
            category=VermogensCategorie.BELEGGING,
        )
        Position.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            quantity=100,
            average_cost_eur=80,
        )

    def test_requires_snapshot(self):
        summary = build_forfaitair_summary(self.user, 2026)
        self.assertFalse(summary["available"])

    def test_computes_after_snapshot(self):
        create_peildatum_snapshot(self.user, 2026)
        summary = build_forfaitair_summary(self.user, 2026)
        self.assertTrue(summary["available"])
        self.assertIn("tax_due_eur", summary)
