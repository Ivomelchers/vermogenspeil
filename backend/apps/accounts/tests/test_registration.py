from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import EmailLog, EmailVerificationToken

User = get_user_model()


@override_settings(
    FRONTEND_URL="http://localhost:5173",
    RESEND_API_KEY="test-key-12345",
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "test-cache",
        }
    }
)
class RegistrationTests(TestCase):
    def setUp(self):
        cache.cache.clear()
        self.client = APIClient()
        self.url = "/api/v1/auth/register/"
        self.payload = {
            "email": "jan@example.com",
            "password": "SecurePass123!",
            "first_name": "Jan",
            "terms_accepted": True,
        }

    @patch("apps.accounts.services.verification.send_email")
    @patch("apps.accounts.serializers.create_auth0_user", return_value="auth0|jan")
    def test_register_creates_user_and_sends_email(self, _mock_auth0, mock_send_email):
        # Mock send_email to return an EmailLog
        mock_log = MagicMock(spec=EmailLog)
        mock_send_email.return_value = mock_log

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIsNone(response.data["error"])
        self.assertFalse(response.data["data"]["email_verified"])

        user = User.objects.get(email="jan@example.com")
        self.assertFalse(user.email_verified)
        self.assertEqual(user.auth_0_id, "auth0|jan")
        self.assertIsNotNone(user.terms_accepted_at)
        self.assertEqual(EmailVerificationToken.objects.filter(user=user).count(), 1)
        # Verify send_email was called
        self.assertTrue(mock_send_email.called)

    def test_register_requires_terms_accepted(self):
        payload = {**self.payload, "terms_accepted": False}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)

    def test_register_rejects_duplicate_email(self):
        User.objects.create_user(
            email="jan@example.com",
            password="SecurePass123!",
            first_name="Bestaand",
        )

        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_rejects_short_password(self):
        payload = {**self.payload, "password": "short"}
        response = self.client.post(self.url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(User.objects.count(), 0)


@override_settings(FRONTEND_URL="http://localhost:5173")
class VerifyEmailTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/verify-email/"
        self.user = User.objects.create_user(
            email="verify@example.com",
            password="SecurePass123!",
            first_name="Verify",
        )
        self.token = EmailVerificationToken.create_for_user(self.user)

    @patch("apps.accounts.authentication.mark_auth0_email_verified")
    def test_verify_email_with_valid_token(self, _mock_mark_verified):
        self.user.auth_0_id = "auth0|verify"
        self.user.save(update_fields=["auth_0_id"])
        response = self.client.post(
            self.url,
            {"token": self.token.token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["email_verified"])

        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        self.assertIsNotNone(self.user.email_verified_at)

        self.token.refresh_from_db()
        self.assertIsNotNone(self.token.used_at)

    def test_verify_email_rejects_invalid_token(self):
        response = self.client.post(
            self.url,
            {"token": "invalid-token"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "invalid_token")

    def test_verify_email_rejects_expired_token(self):
        EmailVerificationToken.objects.filter(pk=self.token.pk).update(
            expires_at=timezone.now() - timedelta(hours=1),
        )

        response = self.client.post(
            self.url,
            {"token": self.token.token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data["error"], "expired_token")


@override_settings(FRONTEND_URL="http://localhost:5173", RESEND_API_KEY="test-key-12345")
class ResendVerificationTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/resend-verification/"

    @patch("apps.accounts.services.verification.send_email")
    def test_resend_sends_new_email_for_unverified_user(self, mock_send_email):
        mock_log = MagicMock(spec=EmailLog)
        mock_send_email.return_value = mock_log

        user = User.objects.create_user(
            email="resend@example.com",
            password="SecurePass123!",
            first_name="Resend",
        )
        EmailVerificationToken.create_for_user(user)

        response = self.client.post(
            self.url,
            {"email": "resend@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_send_email.called)

    @patch("apps.accounts.services.verification.send_email")
    def test_resend_does_not_reveal_unknown_email(self, mock_send_email):
        response = self.client.post(
            self.url,
            {"email": "unknown@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(mock_send_email.called)

    @patch("apps.accounts.services.verification.send_email")
    def test_resend_skips_already_verified_user(self, mock_send_email):
        user = User.objects.create_user(
            email="done@example.com",
            password="SecurePass123!",
            first_name="Done",
        )
        user.email_verified = True
        user.save(update_fields=["email_verified"])

        response = self.client.post(
            self.url,
            {"email": "done@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(mock_send_email.called)
