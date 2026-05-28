import base64

import pyotp
from django.contrib.auth import get_user_model
from django.test import override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.services.totp import confirm_totp_setup, start_totp_setup

User = get_user_model()
TEST_ENCRYPTION_KEY = base64.b64encode(b"0" * 32).decode()


@override_settings(
    ENCRYPTION_KEY=TEST_ENCRYPTION_KEY,
    AUTH0_DOMAIN="dev-test.auth0.com",
    AUTH0_FRONTEND_CLIENT_ID="spa-client-id",
    AUTH0_CONNECTION="Username-Password-Authentication",
)
class TwoFactorTests(APITestCase):
    def setUp(self):
        from unittest.mock import patch

        from apps.accounts.tests.test_auth0 import make_user

        self.make_user = make_user
        self.user = make_user(email="2fa@example.com")
        self.client.credentials(HTTP_AUTHORIZATION="Bearer fake-token")
        self.jwt_patch = patch(
            "apps.accounts.authentication.jwt_decode_token",
            return_value={"sub": self.user.auth_0_id, "email": self.user.email},
        )
        self.jwt_patch.start()

    def tearDown(self):
        self.jwt_patch.stop()

    def test_mfa_status_reflects_local_enrollment(self):
        response = self.client.get("/api/v1/auth/mfa/status/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["data"]["enrolled"])
        self.assertTrue(response.data["data"]["status_available"])

    def test_setup_and_verify_enables_2fa(self):
        setup = start_totp_setup(self.user)
        totp = pyotp.TOTP(setup["secret"])
        otp = totp.now()

        verify_response = self.client.post(
            "/api/v1/auth/2fa/verify/",
            {"otp": otp},
            format="json",
        )

        self.assertEqual(verify_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(verify_response.data["data"]["backup_codes"]), 8)

        self.user.refresh_from_db()
        self.assertTrue(self.user.is_2fa_enabled)

        status_response = self.client.get("/api/v1/auth/mfa/status/")
        self.assertTrue(status_response.data["data"]["enrolled"])

    def test_reset_clears_2fa(self):
        setup = start_totp_setup(self.user)
        confirm_totp_setup(self.user, pyotp.TOTP(setup["secret"]).now())

        response = self.client.post("/api/v1/auth/mfa/reset/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_2fa_enabled)
