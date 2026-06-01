from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.portfolio.models import Asset, Portfolio, VermogensCategorie

User = get_user_model()


class AssetCategoryUpdateTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="cat@test.nl",
            password="SecurePass123!",
        )
        self.portfolio = Portfolio.objects.create(user=self.user, is_default=True)
        self.asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            name="Bitcoin",
            category=VermogensCategorie.BELEGGING,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_patch_category(self):
        response = self.client.patch(
            f"/api/v1/portfolios/assets/{self.asset.id}/category/",
            {"category": VermogensCategorie.BANKTEGOED},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.asset.refresh_from_db()
        self.assertEqual(self.asset.category, VermogensCategorie.BANKTEGOED)
        self.assertEqual(response.json()["data"]["category"], VermogensCategorie.BANKTEGOED)

    def test_patch_unknown_asset_404(self):
        response = self.client.patch(
            "/api/v1/portfolios/assets/99999/category/",
            {"category": VermogensCategorie.SCHULD},
            format="json",
        )
        self.assertEqual(response.status_code, 404)
