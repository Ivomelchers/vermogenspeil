from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from apps.accounts.models import PasswordResetToken
from apps.accounts.services.auth0_login import Auth0LoginError

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


@override_settings(
    AUTH0_DOMAIN="dev-test.auth0.com",
    AUTH0_FRONTEND_CLIENT_ID="spa-client-id",
    AUTH0_CONNECTION="Username-Password-Authentication",
)
class Auth0LoginViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user(email="login@example.com")

    @patch("apps.accounts.views.exchange_password")
    def test_login_returns_tokens(self, mock_exchange):
        mock_exchange.return_value = {
            "id_token": "id-token",
            "access_token": "access-token",
            "refresh_token": "refresh-token",
        }
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["id_token"], "id-token")

    def test_login_blocks_unverified_user(self):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "email_not_verified")

    @patch("apps.accounts.views.exchange_password")
    def test_login_returns_mfa_required(self, mock_exchange):
        mock_exchange.side_effect = Auth0LoginError(
            "mfa_required",
            "Voer uw tweefactorcode in.",
            status_code=403,
            data={"mfa_token": "mfa-token-123"},
        )
        response = self.client.post(
            "/api/v1/auth/login/",
            {"email": "login@example.com", "password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "mfa_required")
        self.assertEqual(response.data["data"]["mfa_token"], "mfa-token-123")


class MfaSettingsTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = make_user()

    @patch("apps.accounts.authentication.jwt_decode_token")
    @patch("apps.accounts.views.get_user_mfa_status")
    def test_mfa_status_returns_enrollment_state(self, mock_status, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        mock_status.return_value = {"enrolled": True}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.get("/api/v1/auth/mfa/status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["data"]["enrolled"])

    @patch("apps.accounts.authentication.jwt_decode_token")
    @patch("apps.accounts.views.exchange_password_for_mfa_setup")
    def test_mfa_enroll_start_returns_mfa_token(self, mock_exchange, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        mock_exchange.side_effect = Auth0LoginError(
            "enrollment_required",
            "Stel tweefactorauthenticatie in.",
            status_code=403,
            data={"mfa_token": "enroll-token"},
        )
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.post(
            "/api/v1/auth/mfa/enroll/start/",
            {"password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["data"]["mfa_token"], "enroll-token")

    @patch("apps.accounts.authentication.jwt_decode_token")
    def test_mfa_enroll_start_rejects_wrong_password(self, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        with patch("apps.accounts.views.exchange_password_for_mfa_setup") as mock_exchange:
            mock_exchange.side_effect = Auth0LoginError(
                "invalid_credentials",
                "Ongeldige inloggegevens.",
                status_code=401,
            )
            response = self.client.post(
                "/api/v1/auth/mfa/enroll/start/",
                {"password": "wrong-password"},
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "invalid_credentials")

    @patch("apps.accounts.authentication.jwt_decode_token")
    @patch("apps.accounts.authentication.requests.get")
    def test_mfa_status_handles_auth0_forbidden(self, mock_get, mock_decode):
        mock_decode.return_value = {"sub": self.user.auth_0_id, "email": self.user.email}
        mock_response = mock_get.return_value
        mock_response.status_code = 403
        mock_response.ok = False
        mock_response.text = "Forbidden"
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")

        response = self.client.get("/api/v1/auth/mfa/status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["enrolled"])
        self.assertFalse(response.data["data"]["status_available"])
