from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, Transaction, TransactionType, VermogensCategorie
from apps.snapshots.lock import is_peildatum_snapshot_locked
from apps.snapshots.models import PeilDatumSnapshot
from apps.snapshots.services.peildatum import create_peildatum_snapshot
from apps.snapshots.services.recalculate import (
    maybe_recalculate_peildatum_snapshots,
    transaction_affects_peildatum_year,
)
from apps.portfolio.services.manual import create_manual_transaction
from apps.pricing.services.price_service import reset_price_service

User = get_user_model()
AMSTERDAM = ZoneInfo("Europe/Amsterdam")
TEST_ENCRYPTION_KEY = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    ENCRYPTION_KEY=TEST_ENCRYPTION_KEY,
)
class PeildatumRecalculateTests(TestCase):
    def setUp(self):
        reset_price_service()
        self.user = User.objects.create_user(
            email="recalc@example.com",
            password="SecurePass123!",
        )
        self.portfolio = Portfolio.objects.create(user=self.user, name="Hoofd", is_default=True)
        self.asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )
        Position.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            quantity=Decimal("1"),
        )

    def tearDown(self):
        reset_price_service()

    def test_transaction_affects_peildatum_year(self):
        dec_2026 = datetime(2026, 12, 15, 12, 0, tzinfo=AMSTERDAM)
        self.assertTrue(transaction_affects_peildatum_year(dec_2026, 2027))
        self.assertFalse(transaction_affects_peildatum_year(dec_2026, 2026))

        feb_2027 = datetime(2027, 2, 1, 12, 0, tzinfo=AMSTERDAM)
        self.assertFalse(transaction_affects_peildatum_year(feb_2027, 2027))

    @patch("apps.snapshots.services.peildatum.portfolio_valuation_at_date")
    def test_recalculate_after_manual_transaction(self, mock_valuation):
        mock_valuation.return_value = {
            "total_value_eur": Decimal("10000"),
            "valuation_method": "historical_prices",
            "historical_priced": 1,
            "total_positions": 1,
            "positions": [],
        }

        snapshot = create_peildatum_snapshot(self.user, 2027)
        self.assertEqual(snapshot.data["total_value_eur"], "10000.00")

        mock_valuation.return_value = {
            "total_value_eur": Decimal("55000"),
            "valuation_method": "historical_prices",
            "historical_priced": 1,
            "total_positions": 1,
            "positions": [],
        }

        occurred = datetime(2026, 11, 1, 10, 0, tzinfo=AMSTERDAM)
        create_manual_transaction(
            self.user,
            portfolio_id=self.portfolio.id,
            asset_id=self.asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("0.5"),
            price_eur=Decimal("40000"),
            occurred_at=occurred,
        )

        snapshot.refresh_from_db()
        self.assertEqual(snapshot.data["total_value_eur"], "55000.00")
        self.assertIn("recalculated_at", snapshot.data)

    @patch("apps.snapshots.services.peildatum.portfolio_valuation_at_date")
    def test_locked_snapshot_not_updated(self, mock_valuation):
        mock_valuation.return_value = {
            "total_value_eur": Decimal("10000"),
            "valuation_method": "historical_prices",
            "historical_priced": 1,
            "total_positions": 1,
            "positions": [],
        }
        year = 2024
        snapshot = create_peildatum_snapshot(self.user, year)
        self.assertTrue(is_peildatum_snapshot_locked(year, on_date=datetime(2025, 6, 1).date()))

        mock_valuation.return_value = {
            "total_value_eur": Decimal("99999"),
            "valuation_method": "historical_prices",
            "historical_priced": 1,
            "total_positions": 1,
            "positions": [],
        }
        occurred = datetime(2023, 6, 1, 10, 0, tzinfo=AMSTERDAM)
        results = maybe_recalculate_peildatum_snapshots(self.user, occurred)
        self.assertTrue(any(r.get("locked") for r in results))

        snapshot.refresh_from_db()
        self.assertEqual(snapshot.data["total_value_eur"], "10000.00")
