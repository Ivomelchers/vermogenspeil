"""
Unit tests for Trading212Client and Trading212Adapter.

Fixtures live in:
  backend/apps/integrations/tests/fixtures/trading212/responses/

The adapter reads these fields from order dicts:
  id, ticker, type, filledQuantity, fillPrice, taxes/fee, dateExecuted
"""

import json
import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.integrations.base import PlatformAdapterError
from apps.integrations.trading212.client import (
    TRADING212_PRODUCTION_URL,
    TRADING212_SANDBOX_URL,
    Trading212APIError,
    Trading212Client,
)
from apps.integrations.trading212.adapter import Trading212Adapter

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "tests", "fixtures", "trading212", "responses"
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


def _make_connection(*, is_demo: bool = False, api_key_encrypted: bytes = b"encrypted-key") -> MagicMock:
    """Return a minimal mock PlatformConnection accepted by Trading212Adapter."""
    conn = MagicMock()
    conn.is_demo = is_demo
    conn.api_key_encrypted = api_key_encrypted
    return conn


# ---------------------------------------------------------------------------
# Trading212Client tests
# ---------------------------------------------------------------------------


class Trading212ClientUrlTests(TestCase):
    """Verify base URL selection logic."""

    def test_client_uses_production_url_by_default(self):
        client = Trading212Client(api_key="tok")
        self.assertEqual(client.base_url, TRADING212_PRODUCTION_URL)

    def test_client_uses_sandbox_url_when_sandbox_true(self):
        client = Trading212Client(api_key="tok", sandbox=True)
        self.assertEqual(client.base_url, TRADING212_SANDBOX_URL)

    def test_client_uses_injected_base_url(self):
        custom = "https://custom.example.com/api/v0"
        client = Trading212Client(api_key="tok", base_url=custom)
        self.assertEqual(client.base_url, custom)

    def test_client_strips_trailing_slash_from_injected_base_url(self):
        client = Trading212Client(api_key="tok", base_url="https://custom.example.com/api/v0/")
        self.assertEqual(client.base_url, "https://custom.example.com/api/v0")


class Trading212ClientFetchPortfolioTests(TestCase):
    """Tests for fetch_portfolio and related parsing."""

    @patch("apps.integrations.trading212.client.requests.request")
    def test_fetch_portfolio_parses_response(self, mock_request):
        fixture = _load_fixture("portfolio_happy_path.json")
        mock_request.return_value = _mock_response(200, fixture)

        client = Trading212Client(api_key="tok")
        positions = client.fetch_portfolio()

        self.assertEqual(len(positions), 3)
        tickers = [p["ticker"] for p in positions]
        self.assertIn("AAPL_US_EQ", tickers)
        self.assertIn("IWDA_EQ", tickers)
        self.assertIn("VUSA_EQ", tickers)

    @patch("apps.integrations.trading212.client.requests.request")
    def test_fetch_portfolio_returns_empty_list_for_empty_response(self, mock_request):
        fixture = _load_fixture("portfolio_empty.json")
        mock_request.return_value = _mock_response(200, fixture)

        positions = Trading212Client(api_key="tok").fetch_portfolio()
        self.assertEqual(positions, [])

    @patch("apps.integrations.trading212.client.requests.request")
    def test_fetch_portfolio_raises_on_401(self, mock_request):
        fixture = _load_fixture("error_401.json")
        mock_request.return_value = _mock_response(401, fixture)

        with self.assertRaises(Trading212APIError) as ctx:
            Trading212Client(api_key="bad-token").fetch_portfolio()

        self.assertEqual(ctx.exception.status_code, 401)

    @patch("apps.integrations.trading212.client.requests.request")
    def test_fetch_portfolio_raises_on_500(self, mock_request):
        fixture = _load_fixture("error_500.json")
        mock_request.return_value = _mock_response(500, fixture)

        with self.assertRaises(Trading212APIError) as ctx:
            Trading212Client(api_key="tok").fetch_portfolio()

        self.assertEqual(ctx.exception.status_code, 500)


class Trading212ClientParsePositionTests(TestCase):
    """Unit tests for the static parse_position helper."""

    def test_parse_position_returns_ticker_and_quantity(self):
        entry = {"ticker": "AAPL_US_EQ", "quantity": "10.0"}
        result = Trading212Client.parse_position(entry)
        self.assertIsNotNone(result)
        ticker, qty = result
        self.assertEqual(ticker, "AAPL_US_EQ")
        self.assertEqual(qty, Decimal("10.0"))

    def test_parse_position_returns_none_for_missing_ticker(self):
        self.assertIsNone(Trading212Client.parse_position({"quantity": "5"}))

    def test_parse_position_returns_none_for_zero_quantity(self):
        self.assertIsNone(Trading212Client.parse_position({"ticker": "AAPL", "quantity": "0"}))

    def test_parse_position_returns_none_for_negative_quantity(self):
        self.assertIsNone(Trading212Client.parse_position({"ticker": "AAPL", "quantity": "-1"}))


# ---------------------------------------------------------------------------
# Trading212Adapter tests
# ---------------------------------------------------------------------------

# Patch target for decrypt_value used inside the adapter's _client() method
_DECRYPT_PATCH = "apps.integrations.trading212.adapter.decrypt_value"


class Trading212AdapterFetchBalancesTests(TestCase):
    """Tests for Trading212Adapter.fetch_balances."""

    def _make_adapter(self, *, is_demo: bool = False) -> Trading212Adapter:
        return Trading212Adapter(connection=_make_connection(is_demo=is_demo))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_portfolio")
    def test_fetch_balances_maps_positions_to_holdings(
        self, mock_portfolio, mock_cash, mock_decrypt
    ):
        mock_portfolio.return_value = [
            {"ticker": "AAPL_US_EQ", "quantity": 10.0},
            {"ticker": "IWDA_EQ", "quantity": 20.0},
        ]
        mock_cash.return_value = {"free": "500.00"}

        adapter = self._make_adapter()
        holdings = adapter.fetch_balances()

        symbols = [h.symbol for h in holdings]
        self.assertIn("AAPL_US_EQ", symbols)
        self.assertIn("IWDA_EQ", symbols)
        # Cash holding should be appended
        self.assertIn("EUR", symbols)

        aapl = next(h for h in holdings if h.symbol == "AAPL_US_EQ")
        self.assertEqual(aapl.quantity, Decimal("10.0"))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_portfolio")
    def test_fetch_balances_empty_portfolio(
        self, mock_portfolio, mock_cash, mock_decrypt
    ):
        mock_portfolio.return_value = []
        mock_cash.return_value = {"free": "0"}

        holdings = self._make_adapter().fetch_balances()
        # No stock positions and zero cash → empty list
        self.assertEqual(holdings, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_portfolio")
    def test_fetch_balances_includes_cash_holding_when_positive(
        self, mock_portfolio, mock_cash, mock_decrypt
    ):
        mock_portfolio.return_value = []
        mock_cash.return_value = {"free": "1234.56"}

        holdings = self._make_adapter().fetch_balances()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].symbol, "EUR")
        self.assertEqual(holdings[0].quantity, Decimal("1234.56"))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_portfolio")
    def test_fetch_balances_skips_positions_with_zero_quantity(
        self, mock_portfolio, mock_cash, mock_decrypt
    ):
        mock_portfolio.return_value = [
            {"ticker": "AAPL_US_EQ", "quantity": 0},
            {"ticker": "IWDA_EQ", "quantity": 5.0},
        ]
        mock_cash.return_value = {"free": "0"}

        holdings = self._make_adapter().fetch_balances()
        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].symbol, "IWDA_EQ")


class Trading212AdapterFetchTransactionsTests(TestCase):
    """Tests for Trading212Adapter.fetch_transactions."""

    def _make_adapter(self) -> Trading212Adapter:
        return Trading212Adapter(connection=_make_connection())

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_buy_order(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "order-001",
                "ticker": "AAPL_US_EQ",
                "type": "MARKET_BUY",
                "filledQuantity": "10",
                "fillPrice": "145.00",
                "taxes": "0",
                "dateExecuted": "2026-01-15T10:30:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()

        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.external_id, "order-001")
        self.assertEqual(rec.symbol, "AAPL_US_EQ")
        self.assertEqual(rec.side, "buy")
        self.assertEqual(rec.transaction_type, "buy")
        self.assertEqual(rec.quantity, Decimal("10"))
        self.assertEqual(rec.price_eur, Decimal("145.00"))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_limit_buy_order(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "order-002",
                "ticker": "IWDA_EQ",
                "type": "LIMIT_BUY",
                "filledQuantity": "5",
                "fillPrice": "80.00",
                "taxes": "0.10",
                "dateExecuted": "2026-02-20T14:45:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].side, "buy")
        self.assertEqual(records[0].transaction_type, "buy")
        self.assertEqual(records[0].fee_eur, Decimal("0.10"))

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_sell_order(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "order-003",
                "ticker": "AAPL_US_EQ",
                "type": "MARKET_SELL",
                "filledQuantity": "3",
                "fillPrice": "160.00",
                "taxes": "0",
                "dateExecuted": "2026-03-01T09:00:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].side, "sell")
        self.assertEqual(records[0].transaction_type, "sell")

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_dividend(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "order-004",
                "ticker": "AAPL_US_EQ",
                "type": "DIVIDEND",
                "filledQuantity": "0",
                "fillPrice": "0",
                "taxes": "0",
                "dateExecuted": "2026-03-10T09:00:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(len(records), 1)
        rec = records[0]
        self.assertEqual(rec.transaction_type, "dividend")
        self.assertEqual(rec.side, "buy")

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_unknown_type_is_skipped(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "order-005",
                "ticker": "AAPL_US_EQ",
                "type": "UNKNOWN_OP",
                "filledQuantity": "1",
                "fillPrice": "100.00",
                "taxes": "0",
                "dateExecuted": "2026-04-01T12:00:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_empty(self, mock_history, mock_decrypt):
        mock_history.return_value = []

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_item_without_id_is_skipped(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "",
                "ticker": "AAPL_US_EQ",
                "type": "MARKET_BUY",
                "filledQuantity": "1",
                "fillPrice": "100.00",
                "taxes": "0",
                "dateExecuted": "2026-04-01T12:00:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_order_history")
    def test_fetch_transactions_total_eur_computed(self, mock_history, mock_decrypt):
        mock_history.return_value = [
            {
                "id": "order-006",
                "ticker": "IWDA_EQ",
                "type": "MARKET_BUY",
                "filledQuantity": "4",
                "fillPrice": "85.00",
                "taxes": "0",
                "dateExecuted": "2026-04-10T10:00:00.000Z",
            }
        ]

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].total_eur, Decimal("340.00"))


class Trading212AdapterValidateConnectionTests(TestCase):
    """Tests for Trading212Adapter.validate_connection."""

    def _make_adapter(self) -> Trading212Adapter:
        return Trading212Adapter(connection=_make_connection())

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash")
    def test_validate_connection_returns_true_on_success(self, mock_cash, mock_decrypt):
        mock_cash.return_value = {"free": "100.00", "total": "100.00"}

        result = self._make_adapter().validate_connection()
        self.assertTrue(result)

    @patch(_DECRYPT_PATCH, return_value="fake-api-key")
    @patch("apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash")
    def test_validate_connection_raises_on_api_failure(self, mock_cash, mock_decrypt):
        mock_cash.side_effect = Trading212APIError("No token in request", status_code=401)

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
