from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.accounts.models import SubscriptionTier

User = get_user_model()


class UserModelTests(TestCase):
    def test_create_user_with_email(self):
        user = User.objects.create_user(
            email="test@example.com",
            password="securepassword12",
            first_name="Jan",
        )

        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Jan")
        self.assertTrue(user.check_password("securepassword12"))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_must_be_unique(self):
        User.objects.create_user(
            email="duplicate@example.com",
            password="securepassword12",
            first_name="Jan",
        )

        with self.assertRaises(Exception):
            User.objects.create_user(
                email="duplicate@example.com",
                password="securepassword12",
                first_name="Piet",
            )

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="securepassword12",
            first_name="Admin",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_username_field_is_email(self):
        self.assertEqual(User.USERNAME_FIELD, "email")

    def test_default_subscription_tier_is_free(self):
        user = User.objects.create_user(
            email="free@example.com",
            password="securepassword12",
            first_name="Free",
        )

        self.assertEqual(user.subscription_tier, SubscriptionTier.FREE)
        self.assertFalse(user.is_premium)

    def test_default_active_tax_year_is_current_year(self):
        user = User.objects.create_user(
            email="year@example.com",
            password="securepassword12",
            first_name="Year",
        )

        self.assertEqual(user.active_tax_year, timezone.now().year)

    def test_full_name_property(self):
        user = User.objects.create_user(
            email="name@example.com",
            password="securepassword12",
            first_name="Jan",
            last_name="Jansen",
        )

        self.assertEqual(user.full_name, "Jan Jansen")

    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(
                email="",
                password="securepassword12",
                first_name="Jan",
            )
