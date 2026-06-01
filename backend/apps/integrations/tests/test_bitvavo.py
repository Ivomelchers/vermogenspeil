import base64
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.integrations.base import BalanceHolding
from apps.integrations.models import PlatformConnection, PlatformType, SyncJob, SyncStatus
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.services.sync import run_connection_sync
from apps.portfolio.models import Asset, Position
from apps.portfolio.services import get_or_create_default_portfolio

User = get_user_model()

TEST_ENCRYPTION_KEY = base64.b64encode(b"0" * 32).decode()


def make_user(**kwargs):
    defaults = {
        "email": "bitvavo@example.com",
        "password": "SecurePass123!",
        "first_name": "Jan",
        "auth_0_id": "auth0|bitvavo-user",
        "email_verified": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


@override_settings(ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BitvavoEncryptionTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_api_credentials_are_encrypted(self):
        portfolio = get_or_create_default_portfolio(self.user)
        connection = PlatformConnection.objects.create(
            user=self.user,
            portfolio=portfolio,
            platform=PlatformType.BITVAVO,
            label="Bitvavo",
        )
        store_api_credentials(
            connection,
            api_key="test-key",
            api_secret="test-secret",
        )
        connection.refresh_from_db()
        self.assertNotIn("test-key", connection.api_key_encrypted)
        self.assertNotIn("test-secret", connection.api_secret_encrypted)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BitvavoAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    @patch("apps.accounts.authentication.jwt_decode_token")
    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter.validate_connection")
    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter.fetch_balances")
    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter.fetch_transactions")
    def test_connect_bitvavo_starts_sync(
        self,
        mock_trades,
        mock_balances,
        mock_validate,
        mock_decode,
    ):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        mock_validate.return_value = True
        mock_balances.return_value = [
            BalanceHolding(symbol="BTC", quantity=Decimal("0.25"), name="BTC"),
        ]
        mock_trades.return_value = []

        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")
        response = self.client.post(
            "/api/v1/integrations/connections/bitvavo/",
            {
                "api_key": "key",
                "api_secret": "secret",
                "label": "Mijn Bitvavo",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["data"]["platform"], PlatformType.BITVAVO)
        self.assertIn("sync_job", response.data["data"])

        connection = PlatformConnection.objects.get(user=self.user)
        self.assertTrue(connection.is_active)

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_connect_blocked_for_unverified_email(self, mock_decode):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.post(
            "/api/v1/integrations/connections/bitvavo/",
            {"api_key": "key", "api_secret": "secret"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "email_not_verified")


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BitvavoSyncTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.portfolio = get_or_create_default_portfolio(self.user)
        self.connection = PlatformConnection.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            platform=PlatformType.BITVAVO,
            label="Bitvavo",
        )
        store_api_credentials(
            self.connection,
            api_key="key",
            api_secret="secret",
        )

    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter.validate_connection")
    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter.fetch_balances")
    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter.fetch_transactions")
    def test_sync_creates_positions(self, mock_trades, mock_balances, mock_validate):
        mock_validate.return_value = True
        mock_balances.return_value = [
            BalanceHolding(symbol="ETH", quantity=Decimal("2"), name="ETH"),
        ]
        mock_trades.return_value = []

        sync_job = SyncJob.objects.create(connection=self.connection)
        run_connection_sync(sync_job.id)

        sync_job.refresh_from_db()
        self.assertEqual(sync_job.status, SyncStatus.SUCCESS)
        self.assertEqual(Position.objects.filter(portfolio=self.portfolio).count(), 1)
        self.assertTrue(Asset.objects.filter(user=self.user, symbol="ETH").exists())
