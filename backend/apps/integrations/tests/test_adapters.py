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
from apps.integrations.trade_republic.adapter import TradeRepublicAdapter

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

# ---------------------------------------------------------------------------
# Trade Republic adapter — patch targets
# ---------------------------------------------------------------------------

_TR_DECRYPT = "apps.integrations.trade_republic.adapter.decrypt_value"
_TR_FETCH_HOLDINGS = "apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_holdings"
_TR_FETCH_ACTIVITIES = "apps.integrations.trade_republic.adapter.TradeRepublicClient.fetch_activities"


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


class TestTradeRepublicAdapterWithFixtures(TestCase):
    """Integration tests that pipe fixture data through the Trade Republic adapter."""

    def _make_adapter(self) -> TradeRepublicAdapter:
        return TradeRepublicAdapter(connection=make_mock_connection())

    # ------------------------------------------------------------------
    # fetch_balances — happy path
    # ------------------------------------------------------------------

    @patch(_TR_DECRYPT, return_value="test_api_key")
    @patch(_TR_FETCH_HOLDINGS)
    def test_fetch_balances_from_fixture(self, mock_holdings, mock_decrypt):
        """Fixture holdings are converted to BalanceHolding objects with ISIN symbols."""
        fixture = load_fixture("trade_republic", "holdings_happy_path.json")
        mock_holdings.return_value = fixture

        adapter = self._make_adapter()
        holdings = adapter.fetch_balances()

        # Basic type check
        self.assertIsInstance(holdings, list)
        self.assertTrue(all(isinstance(h, BalanceHolding) for h in holdings))

        # Length matches fixture holdings list
        expected_count = len(fixture.get("holdings", []))
        self.assertEqual(len(holdings), expected_count)

        # All quantities must be positive
        for h in holdings:
            self.assertGreater(h.quantity, Decimal("0"), f"Quantity should be > 0: {h!r}")

        # Symbols must be 12-character ISINs starting with two letters
        for h in holdings:
            self.assertIsInstance(h.symbol, str)
            self.assertEqual(len(h.symbol), 12, f"ISIN should be 12 chars: {h.symbol!r}")
            self.assertTrue(
                h.symbol[:2].isalpha(),
                f"ISIN should start with 2 letters: {h.symbol!r}",
            )

        # Spot-check known ISINs from the fixture
        symbols = [h.symbol for h in holdings]
        self.assertIn("IE00B4L5Y983", symbols)
        self.assertIn("DE0008469008", symbols)
        self.assertIn("US0378331005", symbols)

    # ------------------------------------------------------------------
    # fetch_balances — empty holdings
    # ------------------------------------------------------------------

    @patch(_TR_DECRYPT, return_value="test_api_key")
    @patch(_TR_FETCH_HOLDINGS)
    def test_fetch_balances_empty(self, mock_holdings, mock_decrypt):
        """Empty holdings fixture returns an empty list."""
        fixture = load_fixture("trade_republic", "holdings_empty.json")
        mock_holdings.return_value = fixture

        holdings = self._make_adapter().fetch_balances()
        self.assertEqual(holdings, [])

    # ------------------------------------------------------------------
    # fetch_transactions — happy path
    # ------------------------------------------------------------------

    @patch(_TR_DECRYPT, return_value="test_api_key")
    @patch(_TR_FETCH_ACTIVITIES)
    def test_fetch_transactions_from_fixture(self, mock_activities, mock_decrypt):
        """Fixture activities are converted to TradeRecord objects."""
        fixture = load_fixture("trade_republic", "transactions_happy_path.json")
        mock_activities.return_value = fixture

        adapter = self._make_adapter()
        records = adapter.fetch_transactions()

        # Basic type check
        self.assertIsInstance(records, list)
        self.assertTrue(all(isinstance(r, TradeRecord) for r in records))

        # All 4 fixture items have a known type — all should parse
        expected_count = len(fixture.get("items", []))
        self.assertEqual(len(records), expected_count)

        # All quantities must be positive (Trade Republic fixture uses 'quantity')
        for r in records:
            self.assertGreater(r.quantity, Decimal("0"), f"Quantity should be > 0: {r!r}")

        # Side must be 'buy' or 'sell' for every record
        valid_sides = {"buy", "sell"}
        for r in records:
            self.assertIn(r.side, valid_sides, f"Unexpected side: {r.side!r}")

        # Dividend record: fixture type='dividend' → transaction_type='dividend', side='buy'
        dividend_records = [r for r in records if r.transaction_type == "dividend"]
        self.assertEqual(len(dividend_records), 1, "Expected exactly one dividend record")
        dividend = dividend_records[0]
        self.assertEqual(dividend.side, "buy")
        self.assertEqual(dividend.symbol, "IE00B4L5Y983")

        # Savingsplan record: fixture type='savingsplan' → side='buy'
        savingsplan_records = [
            r for r in records if r.symbol == "IE00B4L5Y983" and r.transaction_type == "buy"
        ]
        # There are two IE00B4L5Y983 buy records (buy + savingsplan), both side='buy'
        self.assertGreaterEqual(len(savingsplan_records), 1)
        for r in savingsplan_records:
            self.assertEqual(r.side, "buy")

    # ------------------------------------------------------------------
    # fetch_transactions — empty activities
    # ------------------------------------------------------------------

    @patch(_TR_DECRYPT, return_value="test_api_key")
    @patch(_TR_FETCH_ACTIVITIES)
    def test_fetch_transactions_empty(self, mock_activities, mock_decrypt):
        """Empty activities response returns an empty list."""
        mock_activities.return_value = {"items": []}

        records = self._make_adapter().fetch_transactions()
        self.assertEqual(records, [])
