from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.integrations.models import PlatformConnection, SyncStatus
from apps.integrations.services.demo_seed import seed_demo_for_user
from apps.portfolio.models import Asset, Position, Transaction

User = get_user_model()


def make_user(**kwargs):
    defaults = {
        "email": "demo@example.com",
        "password": "SecurePass123!",
        "first_name": "Demo",
        "auth_0_id": "auth0|demo-user",
        "email_verified": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


@override_settings(DEMO_FEATURES_ENABLED=True, CELERY_TASK_ALWAYS_EAGER=True)
class DemoSeedServiceTests(TestCase):
    def setUp(self):
        self.user = make_user()

    def test_seed_creates_demo_connections_and_positions(self):
        result = seed_demo_for_user(self.user)

        self.assertEqual(len(result["connections"]), 2)
        self.assertEqual(PlatformConnection.objects.filter(user=self.user, is_demo=True).count(), 2)
        self.assertGreater(Position.objects.filter(portfolio_id=result["portfolio_id"]).count(), 0)
        self.assertGreater(Transaction.objects.filter(portfolio_id=result["portfolio_id"]).count(), 0)
        self.assertTrue(Asset.objects.filter(user=self.user, symbol="BTC").exists())
        self.assertTrue(Asset.objects.filter(user=self.user, symbol="IWDA").exists())

        for conn in PlatformConnection.objects.filter(user=self.user, is_demo=True):
            self.assertEqual(conn.status, SyncStatus.SUCCESS)


@override_settings(DEMO_FEATURES_ENABLED=True, CELERY_TASK_ALWAYS_EAGER=True)
class DemoSeedAPITests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_demo_seed_endpoint(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.post("/api/v1/integrations/demo/seed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["data"]["connections"]), 2)


@override_settings(DEMO_FEATURES_ENABLED=False)
class DemoDisabledTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_demo_seed_returns_404_when_disabled(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.post("/api/v1/integrations/demo/seed/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
