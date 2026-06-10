"""
Unit tests for TradeRepublicClient and TradeRepublicAdapter.

Fixtures live in:
  backend/apps/integrations/tests/fixtures/trade_republic/responses/

The adapter reads these fields from activity dicts:
  id, isin, type, quantity, price, fee, timestamp
"""

import json
import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.integrations.base import PlatformAdapterError
from apps.integrations.trade_republic.client import (
    TRADE_REPUBLIC_PRODUCTION_URL,
    TradeRepublicAPIError,
    TradeRepublicClient,
)
from apps.integrations.trade_republic.adapter import TradeRepublicAdapter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "tests", "fixtures", "trade_republic", "responses"
)


def _load_fixture(name: str) -> dict | list:
    path = os.path.join(FIXTURES_DIR, name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _mock_response(status_code: int, payload) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = json.dumps(payload)
    resp.json.return_value = payload
    return resp


def _make_connection(*, api_key_encrypted: bytes = b"encrypted-key") -> MagicMock:
    """Return a minimal mock PlatformConnection accepted by TradeRepublicAdapter."""
    conn = MagicMock()
    conn.api_key_encrypted = api_key_encrypted
    return conn


# ---------------------------------------------------------------------------
# TradeRepublicClient tests
# ---------------------------------------------------------------------------


class TradeRepublicClientUrlTests(TestCase):
    """Verify base URL selection logic."""

    def test_client_uses_default_url(self):
        client = TradeRepublicClient(api_key="tok")
        self.assertEqual(client.base_url, TRADE_REPUBLIC_PRODUCTION_URL)

    def test_client_uses_injected_base_url(self):
        custom = "https://custom.example.com/api/v1"
        client = TradeRepublicClient(api_key="tok", base_url=custom)
        self.assertEqual(client.base_url, custom)

    def test_client_strips_trailing_slash_from_injected_base_url(self):
        client = TradeRepublicClient(api_key="tok", base_url="https://custom.example.com/api/v1/")
        self.assertEqual(client.base_url, "https://custom.example.com/api/v1")


class TradeRepublicClientFetchHoldingsTests(TestCase):
    """Tests for fetch_holdings and error handling."""

    @patch("apps.integrations.trade_republic.client.requests.request")
    def test_fetch_holdings_parses_response(self, mock_request):
        fixture = _load_fixture("holdings_happy_path.json")
        mock_request.return_value = _mock_response(200, fixture)

        client = TradeRepublicClient(api_key="tok")
        result = client.fetch_holdings()

        self.assertIn("holdings", result)
        self.assertEqual(len(result["holdings"]), 3)
        isins = [h["isin"] for h in result["holdings"]]
        self.assertIn("IE00B4L5Y983", isins)
        self.assertIn("DE0008469008", isins)
        self.assertIn("US0378331005", isins)

    @patch("apps.integrations.trade_republic.client.requests.request")
    def test_fetch_holdings_raises_on_401(self, mock_request):
        fixture = _load_fixture("error_401.json")
        mock_request.return_value = _mock_response(401, fixture)

        with self.assertRaises(TradeRepublicAPIError) as ctx:
            TradeRepublicClient(api_key="bad-token").fetch_holdings()

        self.assertEqual(ctx.exception.status_code, 401)

    @patch("apps.integrations.trade_republic.client.requests.request")
    def test_fetch_holdings_raises_on_500(self, mock_request):
        fixture = _load_fixture("error_500.json")
        mock_request.return_value = _mock_response(500, fixture)

        with self.assertRaises(TradeRepublicAPIError) as ctx:
            TradeRepublicClient(api_key="tok").fetch_holdings()

        self.assertEqual(ctx.exception.status_code, 500)


class TradeRepublicClientFetchActivitiesTests(TestCase):
    """Tests for fetch_activities."""

    @patch("apps.integrations.trade_republic.client.requests.request")
    def test_fetch_activities_parses_response(self, mock_request):
        fixture = _load_fixture("transactions_happy_path.json")
        mock_request.return_value = _mock_response(200, fixture)

        client = TradeRepublicClient(api_key="tok")
        result = client.fetch_activities()

        self.assertIn("items", result)
        self.assertEqual(len(result["items"]), 4)
        ids = [item["id"] for item in result["items"]]
        self.assertIn("tr_001", ids)
        self.assertIn("tr_004", ids)

    @patch("apps.integrations.trade_republic.client.requests.request")
    def test_fetch_activities_raises_on_401(self, mock_request):
        fixture = _load_fixture("error_401.json")
        mock_request.return_value = _mock_response(401, fixture)

        with self.assertRaises(TradeRepublicAPIError) as ctx:
            TradeRepublicClient(api_key="bad-token").fetch_activities()

        self.assertEqual(ctx.exception.status_code, 401)


class TradeRepublicClientParseHoldingTests(TestCase):
    """Unit tests for the static parse_holding helper."""

    def test_parse_holding_returns_isin_name_and_quantity(self):
        entry = {"isin": "IE00B4L5Y983", "name": "MSCI World ETF", "quantity": "10.0"}
        result = TradeRepublicClient.parse_holding(entry)
        self.assertIsNotNone(result)
        isin, name, qty = result
        self.assertEqual(isin, "IE00B4L5Y983")
        self.assertEqual(name, "MSCI World ETF")
        self.assertEqual(qty, Decimal("10.0"))

    def test_parse_holding_uses_isin_as_name_when_name_missing(self):
        entry = {"isin": "IE00B4L5Y983", "quantity": "5"}
        result = TradeRepublicClient.parse_holding(entry)
        self.assertIsNotNone(result)
        isin, name, qty = result
        self.assertEqual(name, "IE00B4L5Y983")

    def test_parse_holding_returns_none_for_missing_isin(self):
        self.assertIsNone(TradeRepublicClient.parse_holding({"quantity": "5"}))

    def test_parse_holding_returns_none_for_zero_quantity(self):
        self.assertIsNone(TradeRepublicClient.parse_holding({"isin": "IE00B4L5Y983", "quantity": "0"}))

    def test_parse_holding_returns_none_for_negative_quantity(self):
        self.assertIsNone(TradeRepublicClient.parse_holding({"isin": "IE00B4L5Y983", "quantity": "-1"}))


# ---------------------------------------------------------------------------
# TradeRepublicAdapter tests
# ---------------------------------------------------------------------------

# Patch target for decrypt_value used inside the adapter's _client() method
_DECRYPT_PATCH = "apps.integrations.trade_republic.adapter.decrypt_value"


class TradeRepublicAdapterFetchBalancesTests(TestCase):
    """Tests for TradeRepublicAdapter.fetch_balances."""

    def _make_adapter(self) -> TradeRepublicAdapter:
        return TradeRepublicAdapter(connection=_make_connection())

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_holdings")
    def test_fetch_balances_maps_holdings_to_balance_holdings(
        self, mock_holdings, mock_decrypt
    ):
        mock_holdings.return_value = {
            "holdings": [
                {"isin": "IE00B4L5Y983", "name": "MSCI World ETF", "quantity": 20.0},
                {"isin": "DE0008469008", "name": "DAX ETF", "quantity": 5.0},
            ]
        }

        adapter = self._make_adapter()
        holdings = adapter.fetch_balances()

        self.assertEqual(len(holdings), 2)
        symbols = [h.symbol for h in holdings]
        self.assertIn("IE00B4L5Y983", symbols)
        self.assertIn("DE0008469008", symbols)

        msci = next(h for h in holdings if h.symbol == "IE00B4L5Y983")
        self.assertEqual(msci.quantity, Decimal("20.0"))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_holdings")
    def test_fetch_balances_empty(self, mock_holdings, mock_decrypt):
        mock_holdings.return_value = {"holdings": []}

        holdings = self._make_adapter().fetch_balances()
        self.assertEqual(holdings, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_holdings")
    def test_fetch_balances_skips_zero_quantity_holdings(
        self, mock_holdings, mock_decrypt
    ):
        mock_holdings.return_value = {
            "holdings": [
                {"isin": "IE00B4L5Y983", "name": "MSCI World ETF", "quantity": 0},
                {"isin": "DE0008469008", "name": "DAX ETF", "quantity": 5.0},
            ]
        }

        holdings = self._make_adapter().fetch_balances()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].symbol, "DE0008469008")


class TradeRepublicAdapterFetchTransactionsTests(TestCase):
    """Tests for TradeRepublicAdapter.fetch_transactions."""

    def _make_adapter(self) -> TradeRepublicAdapter:
        return TradeRepublicAdapter(connection=_make_connection())

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_buy(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "tr_001",
                    "isin": "IE00B4L5Y983",
                    "type": "buy",
                    "quantity": "10",
                    "price": "80.00",
                    "fee": "0",
                    "timestamp": "2026-01-10T09:30:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()

        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.external_id, "tr_001")
        self.assertEqual(rec.symbol, "IE00B4L5Y983")
        self.assertEqual(rec.side, "buy")
        self.assertEqual(rec.transaction_type, "buy")
        self.assertEqual(rec.quantity, Decimal("10"))
        self.assertEqual(rec.price_eur, Decimal("80.00"))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_savingsplan(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "tr_002",
                    "isin": "IE00B4L5Y983",
                    "type": "savingsplan",
                    "quantity": "10",
                    "price": "82.50",
                    "fee": "0",
                    "timestamp": "2026-02-15T10:00:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()

        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.side, "buy")
        self.assertEqual(rec.transaction_type, "buy")

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_sell(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "tr_003",
                    "isin": "IE00B4L5Y983",
                    "type": "sell",
                    "quantity": "5",
                    "price": "90.00",
                    "fee": "0",
                    "timestamp": "2026-03-01T09:00:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()

        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].side, "sell")
        self.assertEqual(records[0].transaction_type, "sell")

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_dividend(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "tr_004",
                    "isin": "IE00B4L5Y983",
                    "type": "dividend",
                    "quantity": "0.5",
                    "price": "85.00",
                    "fee": "0",
                    "timestamp": "2026-04-01T00:00:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()

        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.side, "buy")
        self.assertEqual(rec.transaction_type, "dividend")

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_unknown_type_skipped(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "tr_005",
                    "isin": "IE00B4L5Y983",
                    "type": "unknown_op",
                    "quantity": "1",
                    "price": "80.00",
                    "fee": "0",
                    "timestamp": "2026-04-10T12:00:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_empty(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {"items": []}

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_item_without_id_is_skipped(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "",
                    "isin": "IE00B4L5Y983",
                    "type": "buy",
                    "quantity": "1",
                    "price": "80.00",
                    "fee": "0",
                    "timestamp": "2026-04-01T12:00:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities")
    def test_fetch_transactions_total_eur_computed(self, mock_activities, mock_decrypt):
        mock_activities.return_value = {
            "items": [
                {
                    "id": "tr_006",
                    "isin": "IE00B4L5Y983",
                    "type": "buy",
                    "quantity": "4",
                    "price": "85.00",
                    "fee": "0",
                    "timestamp": "2026-04-10T10:00:00.000Z",
                }
            ]
        }

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].total_eur, Decimal("340.00"))


class TradeRepublicAdapterValidateConnectionTests(TestCase):
    """Tests for TradeRepublicAdapter.validate_connection."""

    def _make_adapter(self) -> TradeRepublicAdapter:
        return TradeRepublicAdapter(connection=_make_connection())

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_holdings")
    def test_validate_connection_returns_true(self, mock_holdings, mock_decrypt):
        mock_holdings.return_value = {"holdings": []}

        result = self._make_adapter().validate_connection()
        self.assertTrue(result)

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_holdings")
    def test_validate_connection_raises_on_failure(self, mock_holdings, mock_decrypt):
        mock_holdings.side_effect = TradeRepublicAPIError("Unauthorized", status_code=401)

        with self.assertRaises(PlatformAdapterError):
            self._make_adapter().validate_connection()

    @patch(_DECRYPT_PATCH, return_value="")
    def test_validate_connection_raises_when_api_key_empty(self, mock_decrypt):
        with self.assertRaises(PlatformAdapterError):
            self._make_adapter().validate_connection()

    @patch(_DECRYPT_PATCH, side_effect=Exception("decryption failed"))
    def test_validate_connection_raises_on_decryption_error(self, mock_decrypt):
        with self.assertRaises(PlatformAdapterError):
            self._make_adapter().validate_connection()
