from unittest.mock import patch

from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class ProfileUpdateTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email="profile@example.com",
            password="SecurePass123!",
            auth_0_id="auth0|profile-update",
            email_verified=True,
        )

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_patch_fiscal_partner(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.patch(
            "/api/v1/auth/me/",
            {"has_fiscal_partner": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["has_fiscal_partner"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.has_fiscal_partner)

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_complete_onboarding(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")
        self.user.onboarding_completed_at = None
        self.user.save(update_fields=["onboarding_completed_at"])

        response = self.client.patch(
            "/api/v1/auth/me/",
            {"complete_onboarding": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["onboarding_completed"])
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.onboarding_completed_at)
