import base64
import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.integrations.bybit.client import BybitClient
from apps.integrations.bybit.history import execution_to_trade_record
from apps.integrations.models import PlatformConnection, PlatformType, SyncJob, SyncStatus
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.services.sync import run_connection_sync
from apps.portfolio.models import Asset, Position
from apps.portfolio.services import get_or_create_default_portfolio

User = get_user_model()
TEST_ENCRYPTION_KEY = base64.b64encode(b"1" * 32).decode()


def _mock_response(status_code: int, payload: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = json.dumps(payload)
    response.json.return_value = payload
    return response


@override_settings(BYBIT_API_URL="https://api.bybit.com")
class BybitClientTests(TestCase):
    def test_sign_uses_timestamp_key_recv_window_query(self):
        client = BybitClient("my-key", "my-secret")
        timestamp = 1700000000000
        query = "accountType=UNIFIED"
        expected = hmac.new(
            b"my-secret",
            f"{timestamp}my-key{client.recv_window}{query}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(client._sign(timestamp, query), expected)

    @patch("apps.integrations.bybit.client.requests.request")
    def test_get_wallet_balance(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            {
                "retCode": 0,
                "retMsg": "OK",
                "result": {
                    "list": [
                        {
                            "coin": [
                                {"coin": "BTC", "walletBalance": "0.5"},
                                {"coin": "USDT", "walletBalance": "0"},
                            ]
                        }
                    ]
                },
            },
        )
        client = BybitClient("key", "secret")
        coins = client.get_wallet_balance()
        self.assertEqual(len(coins), 2)
        parsed = client.parse_balance(coins[0])
        self.assertEqual(parsed, ("BTC", Decimal("0.5")))

    @patch("apps.integrations.bybit.client.requests.request")
    def test_get_spot_executions_paginates(self, mock_request):
        mock_request.side_effect = [
            _mock_response(
                200,
                {
                    "retCode": 0,
                    "result": {
                        "list": [{"execId": "1", "symbol": "BTCUSDT", "side": "Buy", "execQty": "1", "execPrice": "100", "execFee": "0.1", "execTime": "1700000000000"}],
                        "nextPageCursor": "cursor-2",
                    },
                },
            ),
            _mock_response(
                200,
                {
                    "retCode": 0,
                    "result": {
                        "list": [{"execId": "2", "symbol": "ETHUSDT", "side": "Sell", "execQty": "2", "execPrice": "50", "execFee": "0.2", "execTime": "1700000001000"}],
                        "nextPageCursor": "",
                    },
                },
            ),
        ]
        items = BybitClient("key", "secret").get_spot_executions(limit=1)
        self.assertEqual(len(items), 2)
        self.assertEqual(mock_request.call_count, 2)


class BybitHistoryTests(TestCase):
    def test_execution_to_trade_record(self):
        record = execution_to_trade_record(
            {
                "execId": "abc",
                "symbol": "BTCUSDT",
                "side": "Buy",
                "execQty": "0.01",
                "execPrice": "45000",
                "execFee": "0.5",
                "execTime": "1705312200000",
            }
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.symbol, "BTC")
        self.assertEqual(record.quantity, Decimal("0.01"))


def make_user(**kwargs):
    defaults = {
        "email": "bybit-api@example.com",
        "password": "SecurePass123!",
        "first_name": "Jan",
        "auth_0_id": "auth0|bybit-api-user",
        "email_verified": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class BybitSyncTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.portfolio = get_or_create_default_portfolio(self.user)
        self.connection = PlatformConnection.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            platform=PlatformType.BYBIT,
            label="Bybit",
        )
        store_api_credentials(self.connection, api_key="key", api_secret="secret")

    @patch("apps.integrations.bybit.adapter.BybitClient.get_wallet_balance")
    @patch("apps.integrations.bybit.adapter.BybitClient.get_spot_executions")
    def test_sync_creates_positions_and_trades(self, mock_exec, mock_balance):
        mock_balance.return_value = [{"coin": "ETH", "walletBalance": "2"}]
        mock_exec.return_value = [
            {
                "execId": "t1",
                "symbol": "ETHUSDT",
                "side": "Buy",
                "execQty": "1",
                "execPrice": "3000",
                "execFee": "0.1",
                "execTime": "1705312200000",
            }
        ]

        sync_job = SyncJob.objects.create(connection=self.connection)
        run_connection_sync(sync_job.id)

        sync_job.refresh_from_db()
        self.assertEqual(sync_job.status, SyncStatus.SUCCESS)
        self.assertEqual(Position.objects.filter(portfolio=self.portfolio).count(), 1)
        self.assertTrue(Asset.objects.filter(user=self.user, symbol="ETH").exists())
