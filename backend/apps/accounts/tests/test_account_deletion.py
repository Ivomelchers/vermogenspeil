from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.integrations.models import PlatformConnection
from apps.portfolio.models import Portfolio

User = get_user_model()


class AccountDeletionTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="delete-me@example.com",
            password="SecurePass123!",
            auth_0_id="auth0|delete-me",
            email_verified=True,
        )
        self.portfolio = Portfolio.objects.create(user=self.user, name="Hoofd", is_default=True)
        PlatformConnection.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            platform="bitvavo",
            connection_method="api",
            label="Bitvavo",
            is_active=True,
        )

    @patch("apps.accounts.authentication.jwt_decode_token")
    @patch("apps.accounts.services.account_deletion._try_delete_auth0_user")
    def test_delete_account_soft_deletes_and_anonymizes(self, mock_auth0_del, mock_decode):
        mock_decode.return_value = {"sub": "auth0|delete-me", "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.delete(
            "/api/v1/auth/me/",
            {"confirm_email": "delete-me@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_active)
        self.assertIsNotNone(self.user.deleted_at)
        self.assertTrue(self.user.email.endswith("@deleted.invalid"))
        self.assertIsNone(self.user.auth_0_id)
        conn = PlatformConnection.objects.get(user=self.user)
        self.assertFalse(conn.is_active)

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_delete_requires_matching_email(self, mock_decode):
        mock_decode.return_value = {"sub": "auth0|delete-me", "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.delete(
            "/api/v1/auth/me/",
            {"confirm_email": "wrong@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_active)
