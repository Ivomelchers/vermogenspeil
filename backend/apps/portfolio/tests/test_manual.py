from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.portfolio.models import Asset, AssetType, Position, Transaction, TransactionType
from apps.portfolio.services.manual import create_manual_asset, create_manual_transaction

User = get_user_model()


class ManualEntryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="manual@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )

    def test_create_asset_and_buy_transaction(self):
        asset = create_manual_asset(
            self.user,
            symbol="GOLD",
            name="Goud",
            asset_type=AssetType.METAL,
            category="edelmetaal",
        )
        self.assertEqual(asset.symbol, "GOLD")

        create_manual_transaction(
            self.user,
            asset_id=asset.id,
            transaction_type=TransactionType.BUY,
            quantity=Decimal("2"),
            price_eur=Decimal("100"),
            occurred_at=timezone.now(),
        )

        self.assertEqual(Transaction.objects.filter(portfolio__user=self.user).count(), 1)
        self.assertEqual(Position.objects.filter(portfolio__user=self.user).count(), 1)
