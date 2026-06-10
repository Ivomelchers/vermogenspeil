import base64
import hashlib
import hmac
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from apps.integrations.models import PlatformConnection, PlatformType, SyncJob, SyncStatus
from apps.integrations.okx.client import OkxClient
from apps.integrations.okx.history import fill_to_trade_record
from apps.integrations.services.credentials import store_api_credentials
from apps.integrations.services.sync import run_connection_sync
from apps.portfolio.models import Asset, Position
from apps.portfolio.services import get_or_create_default_portfolio

User = get_user_model()
TEST_ENCRYPTION_KEY = base64.b64encode(b"2" * 32).decode()


def _mock_response(status_code: int, payload: dict) -> MagicMock:
    response = MagicMock()
    response.status_code = status_code
    response.text = json.dumps(payload)
    response.json.return_value = payload
    return response


@override_settings(OKX_API_URL="https://www.okx.com")
class OkxClientTests(TestCase):
    def test_sign_base64_hmac(self):
        client = OkxClient("my-key", "my-secret", "pass")
        timestamp = "1700000000"
        request_path = "/api/v5/account/balance"
        payload = f"{timestamp}GET{request_path}"
        expected = base64.b64encode(
            hmac.new(b"my-secret", payload.encode("utf-8"), hashlib.sha256).digest()
        ).decode("utf-8")
        self.assertEqual(client._sign(timestamp, "GET", request_path), expected)

    @patch("apps.integrations.okx.client.requests.request")
    def test_get_balance(self, mock_request):
        mock_request.return_value = _mock_response(
            200,
            {
                "code": "0",
                "data": [
                    {
                        "details": [
                            {"ccy": "BTC", "cashBal": "1.5"},
                            {"ccy": "EUR", "cashBal": "0"},
                        ]
                    }
                ],
            },
        )
        client = OkxClient("key", "secret", "pass")
        details = client.get_balance()
        self.assertEqual(len(details), 2)
        parsed = client.parse_balance(details[0])
        self.assertEqual(parsed, ("BTC", Decimal("1.5")))

    @patch("apps.integrations.okx.client.requests.request")
    def test_get_spot_fills_paginates(self, mock_request):
        mock_request.side_effect = [
            _mock_response(
                200,
                {
                    "code": "0",
                    "data": [
                        {
                            "tradeId": "100",
                            "instId": "BTC-EUR",
                            "side": "buy",
                            "fillSz": "0.1",
                            "fillPx": "40000",
                            "fee": "0.01",
                            "ts": "1705312200000",
                        }
                    ],
                },
            ),
            _mock_response(
                200,
                {
                    "code": "0",
                    "data": [
                        {
                            "tradeId": "99",
                            "instId": "ETH-EUR",
                            "side": "sell",
                            "fillSz": "0.2",
                            "fillPx": "2500",
                            "fee": "0.02",
                            "ts": "1705398600000",
                        }
                    ],
                },
            ),
            _mock_response(200, {"code": "0", "data": []}),
        ]
        items = OkxClient("key", "secret", "pass").get_spot_fills(limit=1)
        self.assertEqual(len(items), 2)
        self.assertEqual(mock_request.call_count, 3)


class OkxHistoryTests(TestCase):
    def test_fill_to_trade_record(self):
        record = fill_to_trade_record(
            {
                "tradeId": "111",
                "instId": "BTC-EUR",
                "side": "buy",
                "fillSz": "0.01",
                "fillPx": "42000",
                "fee": "0.0001",
                "ts": "1705312200000",
            }
        )
        self.assertIsNotNone(record)
        self.assertEqual(record.symbol, "BTC")
        self.assertEqual(record.quantity, Decimal("0.01"))


def make_user(**kwargs):
    defaults = {
        "email": "okx-api@example.com",
        "password": "SecurePass123!",
        "first_name": "Jan",
        "auth_0_id": "auth0|okx-api-user",
        "email_verified": True,
    }
    defaults.update(kwargs)
    return User.objects.create_user(**defaults)


@override_settings(CELERY_TASK_ALWAYS_EAGER=True, ENCRYPTION_KEY=TEST_ENCRYPTION_KEY)
class OkxSyncTests(TestCase):
    def setUp(self):
        self.user = make_user()
        self.portfolio = get_or_create_default_portfolio(self.user)
        self.connection = PlatformConnection.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            platform=PlatformType.OKX,
            label="OKX",
        )
        store_api_credentials(
            self.connection,
            api_key="key",
            api_secret="secret",
            api_passphrase="passphrase",
        )

    @patch("apps.integrations.okx.adapter.OkxClient.get_balance")
    @patch("apps.integrations.okx.adapter.OkxClient.get_spot_fills")
    def test_sync_creates_positions_and_trades(self, mock_fills, mock_balance):
        mock_balance.return_value = [{"ccy": "ETH", "cashBal": "2"}]
        mock_fills.return_value = [
            {
                "tradeId": "t1",
                "instId": "ETH-EUR",
                "side": "buy",
                "fillSz": "1",
                "fillPx": "3000",
                "fee": "0.1",
                "ts": "1705312200000",
            }
        ]

        sync_job = SyncJob.objects.create(connection=self.connection)
        run_connection_sync(sync_job.id)

        sync_job.refresh_from_db()
        self.assertEqual(sync_job.status, SyncStatus.SUCCESS)
        self.assertEqual(Position.objects.filter(portfolio=self.portfolio).count(), 1)
        self.assertTrue(Asset.objects.filter(user=self.user, symbol="ETH").exists())
