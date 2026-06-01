from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, VermogensCategorie
from apps.portfolio.services.ytd import compute_ytd_summary
from apps.snapshots.models import PeilDatumSnapshot
from apps.snapshots.services.peildatum import create_peildatum_snapshot

User = get_user_model()


@override_settings(CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}})
class YtdSummaryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="ytd@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Hoofd",
            is_default=True,
        )

    @patch("apps.portfolio.services.ytd.fetch_live_prices_for_positions")
    def test_ytd_uses_peildatum_snapshot_as_start(self, mock_live):
        mock_live.return_value = {}
        asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )
        Position.objects.create(portfolio=self.portfolio, asset=asset, quantity=Decimal("1"))

        create_peildatum_snapshot(self.user, 2026)

        with patch(
            "apps.portfolio.services.ytd.position_value_eur",
            return_value=(Decimal("50000"), "market"),
        ):
            summary = compute_ytd_summary(self.portfolio, self.user, year=2026)

        self.assertTrue(summary["available"])
        self.assertEqual(summary["start_method"], "peildatum_snapshot")
