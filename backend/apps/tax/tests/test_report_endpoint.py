from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class Box3ReportEndpointTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="report@test.com",
            password="SecurePass123!",
            auth_0_id="auth0|report-test",
        )
        self.client = APIClient()
        self.url = reverse("tax-box3-report", kwargs={"year": 2026})

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_report_pdf_returns_pdf(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.get(
            self.url,
            {"export": "pdf"},
            HTTP_ACCEPT="application/pdf",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("application/pdf", response["Content-Type"])
        self.assertTrue(response.content.startswith(b"%PDF"))

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_report_json_without_snapshot(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["year"], 2026)

    def test_report_requires_auth(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
