import base64
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.integrations.bitvavo.fixture_client import BitvavoFixtureClient
from apps.integrations.models import PlatformConnection, PlatformType, SyncJob, SyncStatus
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.services.sync import run_connection_sync
from apps.integrations.testing.fixtures import load_json_fixture
from apps.portfolio.models import AssetType, Position, Transaction, TransactionType
from apps.portfolio.services import get_or_create_default_portfolio

User = get_user_model()

TEST_ENCRYPTION_KEY = base64.b64encode(b"0" * 32).decode()


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BitvavoFixtureClientTests(TestCase):
    def test_fixture_files_parseable(self):
        balance = load_json_fixture("bitvavo", "balance.json")
        self.assertEqual(len(balance), 3)
        history = load_json_fixture("bitvavo", "history-all-types.json")
        self.assertEqual(len(history["items"]), 6)

    def test_fixture_client_reads_balance_and_history(self):
        client = BitvavoFixtureClient()
        balance = client.get_balance()
        self.assertTrue(any(row["symbol"] == "BTC" for row in balance))
        history = client.get_account_history()
        self.assertEqual(len(history), 6)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BitvavoFixtureSyncTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="bitvavo-fixture@example.com",
            password="SecurePass123!",
            first_name="Jan",
        )
        self.portfolio = get_or_create_default_portfolio(self.user)
        self.connection = PlatformConnection.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            platform=PlatformType.BITVAVO,
            label="Bitvavo fixture",
        )
        store_api_credentials(
            self.connection,
            api_key="fixture-key",
            api_secret="fixture-secret",
        )

    @patch("apps.integrations.bitvavo.adapter.BitvavoPlatformAdapter._client")
    def test_full_sync_from_account_history_fixtures(self, mock_client):
        mock_client.return_value = BitvavoFixtureClient()
        sync_job = SyncJob.objects.create(connection=self.connection)
        run_connection_sync(sync_job.id)

        sync_job.refresh_from_db()
        self.assertEqual(sync_job.status, SyncStatus.SUCCESS)
        self.assertEqual(sync_job.positions_synced, 3)
        self.assertEqual(sync_job.transactions_synced, 6)

        self.assertTrue(Position.objects.filter(portfolio=self.portfolio, asset__symbol="BTC").exists())
        self.assertTrue(Position.objects.filter(portfolio=self.portfolio, asset__symbol="ETH").exists())
        self.assertTrue(Position.objects.filter(portfolio=self.portfolio, asset__symbol="EUR").exists())

        txs = Transaction.objects.filter(
            portfolio=self.portfolio,
            source_platform=PlatformType.BITVAVO,
        )
        self.assertEqual(txs.count(), 6)
        self.assertEqual(txs.filter(transaction_type=TransactionType.BUY).count(), 2)
        self.assertEqual(txs.filter(transaction_type=TransactionType.SELL).count(), 1)
        self.assertEqual(txs.filter(transaction_type=TransactionType.DEPOSIT).count(), 1)
        self.assertEqual(txs.filter(transaction_type=TransactionType.WITHDRAWAL).count(), 1)
        self.assertEqual(txs.filter(transaction_type=TransactionType.OTHER).count(), 1)

        cash = txs.filter(asset__asset_type=AssetType.CASH)
        self.assertGreaterEqual(cash.count(), 2)
