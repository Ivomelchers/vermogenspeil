from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, VermogensCategorie
from apps.portfolio.services import get_or_create_default_portfolio

User = get_user_model()


class PortfolioModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="portfolio@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_user_owned_queryset_isolates_data(self):
        other = User.objects.create_user(
            email="other@example.com",
            password="SecurePass123!",
            first_name="Piet",
        )
        Portfolio.objects.create(user=self.user, name="Mijn", is_default=True)
        Portfolio.objects.create(user=other, name="Andere", is_default=True)

        self.assertEqual(Portfolio.objects.for_user(self.user).count(), 1)

    def test_get_or_create_default_portfolio(self):
        portfolio = get_or_create_default_portfolio(self.user)
        self.assertTrue(portfolio.is_default)
        again = get_or_create_default_portfolio(self.user)
        self.assertEqual(portfolio.id, again.id)

    def test_position_unique_per_asset(self):
        portfolio = get_or_create_default_portfolio(self.user)
        asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )
        Position.objects.create(portfolio=portfolio, asset=asset, quantity=Decimal("0.5"))
        position, _ = Position.objects.update_or_create(
            portfolio=portfolio,
            asset=asset,
            defaults={"quantity": Decimal("1.0")},
        )
        self.assertEqual(position.quantity, Decimal("1.0"))
