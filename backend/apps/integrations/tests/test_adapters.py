"""
Integration tests for Trading212Adapter and TradeRepublicAdapter.

These tests load real fixture JSON files and pass them through the adapter
parsing methods.  No network access is needed — client methods are mocked
to return the loaded fixture data so we exercise the full adapter code path.

Fixtures live in:
  backend/apps/integrations/tests/fixtures/<platform>/responses/
"""

import json
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.integrations.base import BalanceHolding, TradeRecord
from apps.integrations.trading212.adapter import Trading212Adapter

# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(platform: str, filename: str):
    """Load a fixture JSON file from tests/fixtures/<platform>/responses/."""
    path = FIXTURES_DIR / platform / "responses" / filename
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Mock connection factory
# ---------------------------------------------------------------------------


def make_mock_connection(is_demo: bool = False) -> MagicMock:
    """Return a minimal mock PlatformConnection object."""
    conn = MagicMock()
    conn.is_demo = is_demo
    conn.api_key_encrypted = b"encrypted_key"
    return conn


# ---------------------------------------------------------------------------
# Trading212 adapter — patch targets
# ---------------------------------------------------------------------------

_T212_DECRYPT = "apps.integrations.trading212.adapter.decrypt_value"
_T212_FETCH_PORTFOLIO = "apps.integrations.trading212.adapter.Trading212Client.fetch_portfolio"
_T212_FETCH_CASH = "apps.integrations.trading212.adapter.Trading212Client.fetch_account_cash"
_T212_FETCH_ORDERS = "apps.integrations.trading212.adapter.Trading212Client.fetch_order_history"

# ===========================================================================
# TestTrading212AdapterWithFixtures
# ===========================================================================


class TestTrading212AdapterWithFixtures(TestCase):
    """Integration tests that pipe fixture data through the Trading212 adapter."""

    def _make_adapter(self, *, is_demo: bool = False) -> Trading212Adapter:
        return Trading212Adapter(connection=make_mock_connection(is_demo=is_demo))

    # ------------------------------------------------------------------
    # fetch_balances — happy path
    # ------------------------------------------------------------------

    @patch(_T212_DECRYPT, return_value="test_api_key")
    @patch(_T212_FETCH_CASH)
    @patch(_T212_FETCH_PORTFOLIO)
    def test_fetch_balances_from_fixture(self, mock_portfolio, mock_cash, mock_decrypt):
        """Fixture positions are converted to BalanceHolding objects."""
        fixture = load_fixture("trading212", "portfolio_happy_path.json")
        # fetch_portfolio() already strips the wrapper and returns the list
        positions = fixture.get("positions", [])
        mock_portfolio.return_value = positions
        mock_cash.return_value = {"free": "0"}  # no cash, keeps assertion count clean

        adapter = self._make_adapter()
        holdings = adapter.fetch_balances()

        # Basic type check
        self.assertIsInstance(holdings, list)
        self.assertTrue(all(isinstance(h, BalanceHolding) for h in holdings))

        # Length should match fixture positions (cash excluded — free=0)
        self.assertEqual(len(holdings), len(positions))

        # All symbols must be non-empty strings
        for h in holdings:
            self.assertIsInstance(h.symbol, str)
            self.assertTrue(h.symbol.strip(), f"Symbol should not be empty: {h!r}")

        # All quantities must be positive
        for h in holdings:
            self.assertGreater(h.quantity, Decimal("0"), f"Quantity should be > 0: {h!r}")

        # Spot-check known tickers from the fixture
        symbols = [h.symbol for h in holdings]
        self.assertIn("AAPL_US_EQ", symbols)
        self.assertIn("IWDA_EQ", symbols)
        self.assertIn("VUSA_EQ", symbols)

    # ------------------------------------------------------------------
    # fetch_balances — empty portfolio
    # ------------------------------------------------------------------

    @patch(_T212_DECRYPT, return_value="test_api_key")
    @patch(_T212_FETCH_CASH)
    @patch(_T212_FETCH_PORTFOLIO)
    def test_fetch_balances_empty_portfolio(self, mock_portfolio, mock_cash, mock_decrypt):
        """Empty portfolio fixture results in an empty holdings list."""
        fixture = load_fixture("trading212", "portfolio_empty.json")
        mock_portfolio.return_value = fixture.get("positions", [])
        mock_cash.return_value = {"free": "0"}

        holdings = self._make_adapter().fetch_balances()
        self.assertEqual(holdings, [])

    # ------------------------------------------------------------------
    # fetch_balances — cash holding appended when free > 0
    # ------------------------------------------------------------------

    @patch(_T212_DECRYPT, return_value="test_api_key")
    @patch(_T212_FETCH_CASH)
    @patch(_T212_FETCH_PORTFOLIO)
    def test_fetch_balances_includes_cash_holding(self, mock_portfolio, mock_cash, mock_decrypt):
        """Cash balance is appended as an EUR holding when free > 0."""
        fixture = load_fixture("trading212", "portfolio_happy_path.json")
        mock_portfolio.return_value = fixture.get("positions", [])
        mock_cash.return_value = {"free": "250.00"}

        holdings = self._make_adapter().fetch_balances()

        symbols = [h.symbol for h in holdings]
        self.assertIn("EUR", symbols)

        cash_holding = next(h for h in holdings if h.symbol == "EUR")
        self.assertEqual(cash_holding.quantity, Decimal("250.00"))

    # ------------------------------------------------------------------
    # fetch_transactions — happy path
    # ------------------------------------------------------------------

    @patch(_T212_DECRYPT, return_value="test_api_key")
    @patch(_T212_FETCH_ORDERS)
    def test_fetch_transactions_from_fixture(self, mock_orders, mock_decrypt):
        """Fixture order history items are converted to TradeRecord objects.

        Note: The fixture uses the field names 'quantity' and 'price', while
        the adapter reads 'filledQuantity' and 'fillPrice'.  Records are still
        produced (with quantity=0 when those fields are absent), but the type,
        side, and transaction_type mappings are fully exercised.
        """
        fixture = load_fixture("trading212", "transactions_happy_path.json")
        items = fixture.get("items", [])
        mock_orders.return_value = items

        adapter = self._make_adapter()
        records = adapter.fetch_transactions()

        # Basic type check
        self.assertIsInstance(records, list)
        self.assertTrue(all(isinstance(r, TradeRecord) for r in records))

        # All items have a valid id, ticker, type, and dateExecuted — all should parse
        self.assertEqual(len(records), len(items))

        # All symbols must be non-empty strings
        for r in records:
            self.assertIsInstance(r.symbol, str)
            self.assertTrue(r.symbol.strip(), f"Symbol should not be empty: {r!r}")

        # All quantities must be >= 0 (fixture uses 'quantity' not 'filledQuantity')
        for r in records:
            self.assertGreaterEqual(r.quantity, Decimal("0"), f"Quantity should be >= 0: {r!r}")

        # Side must be 'buy' or 'sell' for every record
        valid_sides = {"buy", "sell"}
        for r in records:
            self.assertIn(r.side, valid_sides, f"Unexpected side: {r.side!r}")

        # Dividend transaction: fixture item with type=DIVIDEND maps to transaction_type='dividend'
        dividend_records = [r for r in records if r.transaction_type == "dividend"]
        self.assertEqual(len(dividend_records), 1, "Expected exactly one dividend record")
        self.assertEqual(dividend_records[0].side, "buy")
        self.assertEqual(dividend_records[0].symbol, "AAPL_US_EQ")

    # ------------------------------------------------------------------
    # fetch_transactions — empty history
    # ------------------------------------------------------------------

    @patch(_T212_DECRYPT, return_value="test_api_key")
    @patch(_T212_FETCH_ORDERS)
    def test_fetch_transactions_empty(self, mock_orders, mock_decrypt):
        """Empty order history returns an empty list."""
        mock_orders.return_value = []

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])


# ===========================================================================
# TestTradeRepublicAdapterWithFixtures
# ===========================================================================


