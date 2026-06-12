"""Tests for Saxo API adapter."""

from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.test import TestCase

from apps.accounts.utils.encryption import encrypt_value
from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformType
from apps.integrations.saxo.adapter import SaxoPlatformAdapter
from apps.integrations.saxo.client import SaxoAPIError
from apps.portfolio.models import AssetType, Portfolio


class SaxoAdapterTestCase(TestCase):
    def setUp(self):
        from apps.accounts.models import User

        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
        )
        self.portfolio = Portfolio.objects.create(
            user=self.user,
            name="Test Portfolio",
        )

    def _create_connection(self, access_token: str = "test_token", refresh_token: str = "test_refresh"):
        """Create a test platform connection."""
        return PlatformConnection.objects.create(
            user=self.user,
            portfolio=self.portfolio,
            platform=PlatformType.SAXO,
            connection_method=ConnectionMethod.API,
            api_key_encrypted=encrypt_value(access_token),
            api_secret_encrypted=encrypt_value(refresh_token),
        )

    @patch("apps.integrations.saxo.adapter.SaxoClient")
    def test_validate_connection_success(self, mock_client_cls):
        """Test successful connection validation."""
        mock_client = MagicMock()
        mock_client.get_client_me.return_value = {"ClientKey": "test_client_123"}
        mock_client_cls.return_value = mock_client

        connection = self._create_connection()
        adapter = SaxoPlatformAdapter(connection)

        assert adapter.validate_connection() is True
        mock_client.get_client_me.assert_called_once()

    @patch("apps.integrations.saxo.adapter.SaxoClient")
    def test_validate_connection_failure(self, mock_client_cls):
        """Test connection validation failure."""
        mock_client = MagicMock()
        mock_client.get_client_me.side_effect = SaxoAPIError("Invalid token")
        mock_client_cls.return_value = mock_client

        connection = self._create_connection()
        adapter = SaxoPlatformAdapter(connection)

        with self.assertRaises(Exception) as ctx:
            adapter.validate_connection()
        assert "mislukt" in str(ctx.exception).lower()

    @patch("apps.integrations.saxo.adapter.SaxoClient")
    def test_fetch_balances(self, mock_client_cls):
        """Test fetching balances."""
        mock_client = MagicMock()
        mock_client.get_client_me.return_value = {"ClientKey": "test_client_123"}
        mock_client.get_accounts.return_value = [
            {"AccountKey": "acc_123", "AccountId": "Account 1"},
        ]
        mock_client.get_positions.return_value = [
            {
                "Uic": "IWDA",
                "Identifier": "IWDA",
                "NetPosition": 10.0,
                "AssetType": "Stock",
                "DisplayAndFormat": {"Description": "iShares Core MSCI World"},
            },
            {
                "Uic": "ASML",
                "Identifier": "ASML",
                "NetPosition": 5.0,
                "AssetType": "Stock",
                "DisplayAndFormat": {"Description": "ASML Holding NV"},
            },
        ]
        mock_client_cls.return_value = mock_client

        connection = self._create_connection()
        adapter = SaxoPlatformAdapter(connection)

        balances = adapter.fetch_balances()

        assert len(balances) == 2
        assert balances[0].symbol == "IWDA"
        assert balances[0].quantity == Decimal("10")
        assert balances[1].symbol == "ASML"

    @patch("apps.integrations.saxo.adapter.SaxoClient")
    def test_fetch_transactions(self, mock_client_cls):
        """Test fetching transactions."""
        mock_client = MagicMock()
        mock_client.get_client_me.return_value = {"ClientKey": "test_client_123"}
        mock_client.get_accounts.return_value = [
            {"AccountKey": "acc_123", "AccountId": "Account 1"},
        ]
        mock_client.get_trades.return_value = [
            {
                "TradeId": "trade_123",
                "Uic": "IWDA",
                "Identifier": "IWDA",
                "BuySell": "BUY",
                "Amount": 10.0,
                "OpenPrice": 100.50,
                "CostAmount": 5.00,
                "AssetType": "Stock",
                "ExecutionTime": "2026-01-01T09:30:00Z",
            },
            {
                "TradeId": "trade_124",
                "Uic": "ASML",
                "Identifier": "ASML",
                "BuySell": "SELL",
                "Amount": 5.0,
                "OpenPrice": 250.75,
                "CostAmount": 10.00,
                "AssetType": "Stock",
                "ExecutionTime": "2026-01-02T10:15:00Z",
            },
        ]
        mock_client_cls.return_value = mock_client

        connection = self._create_connection()
        adapter = SaxoPlatformAdapter(connection)

        trades = adapter.fetch_transactions()

        assert len(trades) == 2
        assert trades[0].symbol == "IWDA"
        assert trades[0].side == "BUY"
        assert trades[0].quantity == Decimal("10")
        assert trades[1].side == "SELL"

    @patch("apps.integrations.saxo.adapter.SaxoClient")
    def test_fetch_empty_positions(self, mock_client_cls):
        """Test that zero positions are filtered out."""
        mock_client = MagicMock()
        mock_client.get_client_me.return_value = {"ClientKey": "test_client_123"}
        mock_client.get_accounts.return_value = [
            {"AccountKey": "acc_123", "AccountId": "Account 1"},
        ]
        mock_client.get_positions.return_value = [
            {
                "Uic": "IWDA",
                "NetPosition": 0.0,  # Zero position
                "AssetType": "Stock",
                "DisplayAndFormat": {"Description": "iShares Core MSCI World"},
            },
        ]
        mock_client_cls.return_value = mock_client

        connection = self._create_connection()
        adapter = SaxoPlatformAdapter(connection)

        balances = adapter.fetch_balances()

        assert len(balances) == 0
