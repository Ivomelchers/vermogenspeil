from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import PasswordResetToken

User = get_user_model()


def make_user(**kwargs):
    defaults = {
        "email": "user@example.com",
        "password": "SecurePass123!",
        "first_name": "Test",
        "auth_0_id": "auth0|test-user",
        "email_verified": True,
    }
    defaults.update(kwargs)
    password = defaults.pop("password", None)
    user = User.objects.create_user(**defaults)
    if password:
        user.set_password(password)
        user.save(update_fields=["password"])
    else:
        user.set_unusable_password()
        user.save(update_fields=["password"])
    return user


class Auth0MeTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_me_returns_profile_for_verified_user(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["email"], self.user.email)

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_me_blocks_unverified_user(self, mock_decode):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.get("/api/v1/auth/me/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "email_not_verified")


@override_settings(FRONTEND_URL="http://localhost:5173")
class Auth0RegistrationTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/register/"
        self.payload = {
            "email": "jan@example.com",
            "password": "SecurePass123!",
            "first_name": "Jan",
            "terms_accepted": True,
        }

    @patch("apps.accounts.serializers.create_auth0_user", return_value="auth0|jan")
    def test_register_creates_user_and_sends_email(self, _mock_auth0):
        response = self.client.post(self.url, self.payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertFalse(response.data["data"]["email_verified"])
        self.assertEqual(len(mail.outbox), 1)

        user = User.objects.get(email="jan@example.com")
        self.assertEqual(user.auth_0_id, "auth0|jan")


@override_settings(FRONTEND_URL="http://localhost:5173", PASSWORD_RESET_TOKEN_HOURS=1)
class Auth0PasswordResetTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email="reset@example.com", auth_0_id="auth0|reset")

    def test_reset_request_sends_email_for_known_user(self):
        mail.outbox.clear()
        response = self.client.post(
            "/api/v1/auth/password/reset/",
            {"email": "reset@example.com"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), 1)

    @patch("apps.accounts.services.password_reset.update_user_password")
    def test_validate_and_confirm_reset_token(self, mock_update_password):
        import hashlib

        plain_token = "abc123reset"
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        PasswordResetToken.objects.create(user=self.user, token=hashed_token)

        validate_response = self.client.get(
            f"/api/v1/auth/password/reset/{plain_token}/",
        )
        self.assertEqual(validate_response.status_code, status.HTTP_200_OK)

        confirm_response = self.client.post(
            f"/api/v1/auth/password/reset/{plain_token}/",
            {"password": "NewSecurePass456!"},
            format="json",
        )
        self.assertEqual(confirm_response.status_code, status.HTTP_200_OK)
        mock_update_password.assert_called_once_with(
            self.user.auth_0_id,
            "NewSecurePass456!",
        )

    @patch("apps.accounts.services.password_reset.update_user_password")
    def test_password_reset_does_not_remove_auth0_link(self, _mock_update_password):
        import hashlib

        plain_token = "reset456token"
        hashed_token = hashlib.sha256(plain_token.encode()).hexdigest()
        PasswordResetToken.objects.create(user=self.user, token=hashed_token)

        self.client.post(
            f"/api/v1/auth/password/reset/{plain_token}/",
            {"password": "NewSecurePass456!"},
            format="json",
        )

        self.user.refresh_from_db()
        self.assertEqual(self.user.auth_0_id, "auth0|reset")
