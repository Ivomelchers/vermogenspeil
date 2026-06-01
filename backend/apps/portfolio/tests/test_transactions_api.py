from datetime import datetime, timezone as dt_timezone

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.portfolio.models import Asset, AssetType, Portfolio, Transaction, TransactionType, VermogensCategorie
from apps.portfolio.services import get_or_create_default_portfolio
from apps.portfolio.services.dedupe import dedupe_portfolio_transactions
from apps.portfolio.services.transactions_list import list_portfolio_transactions

User = get_user_model()


class TransactionsListServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="tx-list@example.com",
            password="SecurePass123!",
        )
        self.portfolio = get_or_create_default_portfolio(self.user)
        self.asset = Asset.objects.create(
            user=self.user,
            symbol="BTC",
            name="Bitcoin",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )

    def _create_tx(
        self,
        *,
        external_id: str,
        platform: str = "bitvavo",
        day: int = 1,
        tx_hash_suffix: str = "a",
    ):
        occurred = datetime(2026, 1, day, 12, 0, tzinfo=dt_timezone.utc)
        Transaction.objects.create(
            portfolio=self.portfolio,
            asset=self.asset,
            transaction_type=TransactionType.BUY,
            quantity=1,
            price_eur=100,
            occurred_at=occurred,
            external_id=external_id,
            transaction_hash=f"hash-{external_id}-{tx_hash_suffix}",
            source_platform=platform,
        )

    def test_pagination_and_platform_filter(self):
        self._create_tx(external_id="a", platform="bitvavo", day=1)
        self._create_tx(external_id="b", platform="degiro", day=2)

        result = list_portfolio_transactions(
            self.portfolio,
            page=1,
            page_size=1,
            platform="bitvavo",
        )
        self.assertEqual(result["total"], 1)
        self.assertEqual(len(result["items"]), 1)
        self.assertEqual(result["items"][0].source_platform, "bitvavo")

    def test_dedupe_by_external_id(self):
        self._create_tx(external_id="dup-1", day=1, tx_hash_suffix="a")
        self._create_tx(external_id="dup-1", day=1, tx_hash_suffix="b")
        self._create_tx(external_id="unique-1", day=2)

        result = dedupe_portfolio_transactions(self.portfolio)
        self.assertEqual(result["removed"], 1)
        self.assertEqual(self.portfolio.transactions.count(), 2)
