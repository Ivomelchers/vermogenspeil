from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, VermogensCategorie
from apps.snapshots.exceptions import SnapshotAlreadyExistsError
from apps.snapshots.models import PeilDatumSnapshot
from apps.snapshots.services.peildatum import (
    create_peildatum_snapshot,
    peildatum_instant_cet,
)
from apps.pricing.services.price_service import PriceQuote, reset_price_service

User = get_user_model()
TEST_ENCRYPTION_KEY = "MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA="


class PeildatumTimezoneTests(TestCase):
    def test_peildatum_is_midnight_amsterdam_not_utc(self):
        instant = peildatum_instant_cet(2026)
        self.assertEqual(instant.tzinfo, ZoneInfo("Europe/Amsterdam"))
        self.assertEqual(instant.hour, 0)
        self.assertEqual(instant.day, 1)
        self.assertEqual(instant.month, 1)

        utc_equivalent = instant.astimezone(ZoneInfo("UTC"))
        # Winter (CET): 1 jan 00:00 Amsterdam = 31 dec 23:00 UTC
        self.assertEqual(utc_equivalent, datetime(2025, 12, 31, 23, 0, tzinfo=ZoneInfo("UTC")))


@override_settings(
    CACHES={"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}},
    ENCRYPTION_KEY=TEST_ENCRYPTION_KEY,
)
class PeildatumSnapshotModelTests(TestCase):
    def setUp(self):
        reset_price_service()
        self.user = User.objects.create_user(
            email="peil@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def tearDown(self):
        reset_price_service()

    @patch("apps.snapshots.services.peildatum.portfolio_valuation_at_date")
    def test_snapshot_immutable_after_create(self, mock_valuation):
        portfolio = Portfolio.objects.create(user=self.user, name="Hoofd", is_default=True)
        asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )
        position = Position.objects.create(portfolio=portfolio, asset=asset, quantity=Decimal("1"))
        mock_valuation.return_value = {
            "total_value_eur": Decimal("50000"),
            "valuation_method": "historical_prices",
            "historical_priced": 1,
            "total_positions": 1,
            "positions": [
                {
                    "position": position,
                    "quantity": Decimal("1"),
                    "value_eur": Decimal("50000"),
                    "valuation_source": "historical",
                    "unit_price_eur": Decimal("50000"),
                }
            ],
        }

        snapshot = create_peildatum_snapshot(self.user, 2026)
        self.assertEqual(snapshot.year, 2026)
        self.assertIn("peildatum", snapshot.data)
        self.assertEqual(snapshot.data["valuation_at_peildatum"], "historical_prices")
        self.assertEqual(snapshot.data["box3_totals"]["overige_bezittingen_eur"], "50000.00")
        mock_valuation.assert_called_once()

        with self.assertRaises(SnapshotAlreadyExistsError):
            create_peildatum_snapshot(self.user, 2026)

        snapshot.data = {**snapshot.data, "total_value_eur": "60000.00"}
        snapshot.save(update_fields=["data", "updated_at"])
        snapshot.refresh_from_db()
        self.assertEqual(snapshot.data["total_value_eur"], "60000.00")

        with self.assertRaises(ValueError):
            snapshot.delete()

    def test_payload_peildatum_field_uses_cet(self):
        snapshot = create_peildatum_snapshot(self.user, 2025)
        peildatum_str = snapshot.data["peildatum"]
        self.assertTrue(peildatum_str.startswith("2025-01-01T00:00:00"))


@override_settings(ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class PeildatumAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="peil-api@example.com",
            password="SecurePass123!",
            first_name="Jan",
            auth_0_id="auth0|peil-api",
        )

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_create_and_list_snapshot(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.post(
            "/api/v1/snapshots/peildatum/create/",
            {"year": timezone.now().year},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["year"], timezone.now().year)

        list_response = self.client.get("/api/v1/snapshots/peildatum/")
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data["data"]), 1)

        duplicate = self.client.post(
            "/api/v1/snapshots/peildatum/create/",
            {"year": timezone.now().year},
            format="json",
        )
        self.assertEqual(duplicate.status_code, status.HTTP_409_CONFLICT)
