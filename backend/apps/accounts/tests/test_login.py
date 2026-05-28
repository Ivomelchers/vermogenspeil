from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

User = get_user_model()


class LoginTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = "/api/v1/auth/login/"
        self.user = User.objects.create_user(
            email="login@example.com",
            password="SecurePass123!",
            first_name="Login",
            email_verified=True,
        )

    def test_login_returns_jwt_for_verified_user(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])
        self.assertIn("refresh", response.data["data"])
        self.assertIsNone(response.data["error"])

    def test_login_rejects_unverified_user(self):
        self.user.email_verified = False
        self.user.save(update_fields=["email_verified"])

        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "SecurePass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data["error"], "email_not_verified")

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            self.url,
            {"email": "login@example.com", "password": "WrongPassword123!"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["error"], "invalid_credentials")


class TokenRefreshTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login/"
        self.refresh_url = "/api/v1/auth/token/refresh/"
        User.objects.create_user(
            email="refresh@example.com",
            password="SecurePass123!",
            first_name="Refresh",
            email_verified=True,
        )
        login_response = self.client.post(
            self.login_url,
            {"email": "refresh@example.com", "password": "SecurePass123!"},
            format="json",
        )
        self.refresh_token = login_response.data["data"]["refresh"]

    def test_refresh_returns_new_access_token(self):
        response = self.client.post(
            self.refresh_url,
            {"refresh": self.refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data["data"])


class LogoutTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = "/api/v1/auth/login/"
        self.logout_url = "/api/v1/auth/logout/"
        User.objects.create_user(
            email="logout@example.com",
            password="SecurePass123!",
            first_name="Logout",
            email_verified=True,
        )
        login_response = self.client.post(
            self.login_url,
            {"email": "logout@example.com", "password": "SecurePass123!"},
            format="json",
        )
        self.access_token = login_response.data["data"]["access"]
        self.refresh_token = login_response.data["data"]["refresh"]

    def test_logout_blacklists_refresh_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(
            self.logout_url,
            {"refresh": self.refresh_token},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        refresh_response = self.client.post(
            "/api/v1/auth/token/refresh/",
            {"refresh": self.refresh_token},
            format="json",
        )
        self.assertEqual(refresh_response.status_code, status.HTTP_400_BAD_REQUEST)
