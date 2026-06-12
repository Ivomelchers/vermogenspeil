import requests
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Any


class SaxoAPIError(Exception):
    """Saxo API error."""
    pass


class SaxoClient:
    """Saxo Bank OpenAPI client."""

    BASE_URL = "https://gateway.saxobank.com/sim/openapi"

    def __init__(self, access_token: str | None = None, api_key: str | None = None, refresh_token: str | None = None):
        """
        Initialize Saxo client with either OAuth token or API key.

        Args:
            access_token: OAuth2 access token (for OAuth method)
            api_key: API key (for API key method)
            refresh_token: OAuth2 refresh token (optional)
        """
        self.access_token = access_token
        self.api_key = api_key
        self.refresh_token = refresh_token
        self.session = requests.Session()

        # Set authorization header based on method
        if access_token:
            self.session.headers.update({
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            })
        elif api_key:
            self.session.headers.update({
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            })
        else:
            raise SaxoAPIError("Either access_token or api_key must be provided")

    def _request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any]:
        """Make HTTP request to Saxo API."""
        url = f"{self.BASE_URL}/{endpoint}"
        try:
            response = self.session.request(method, url, timeout=10, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as exc:
            raise SaxoAPIError(f"Saxo API error: {exc}") from exc

    def get_client_me(self) -> dict[str, Any]:
        """Get current client info."""
        return self._request("GET", "port/v1/clients/me")

    def get_accounts(self, client_key: str) -> list[dict[str, Any]]:
        """Get list of accounts for client."""
        result = self._request("GET", "port/v1/accounts", params={"ClientKey": client_key})
        return result.get("Data", [])

    def get_balances(self, account_key: str | None = None, client_key: str | None = None) -> dict[str, Any]:
        """Get account balances (cash, positions, margin)."""
        params = {}
        if account_key:
            params["AccountKey"] = account_key
        elif client_key:
            params["ClientKey"] = client_key

        return self._request("GET", "port/v1/balances", params=params)

    def get_positions(self, account_key: str | None = None, client_key: str | None = None) -> list[dict[str, Any]]:
        """Get open positions."""
        params = {}
        if account_key:
            endpoint = f"port/v1/positions/{account_key}"
        elif client_key:
            endpoint = f"port/v1/positions/ClientKey={client_key}"
        else:
            endpoint = "port/v1/positions/me"

        result = self._request("GET", endpoint, params=params)
        return result.get("Data", [])

    def get_trades(self, account_key: str | None = None, client_key: str | None = None, skip: int = 0, count: int = 100) -> list[dict[str, Any]]:
        """Get executed trades via reports API."""
        params = {"$skip": skip, "$top": count}

        # Use reports endpoint (most reliable)
        if client_key:
            endpoint = f"cs/v1/reports/trades/{client_key}"
        elif account_key:
            # Fallback: try the direct trades endpoint
            endpoint = f"trade/v2/trades/{account_key}"
            params = {"$skip": skip, "$count": count}
        else:
            # Try /me variant
            endpoint = "trade/v2/trades/me"
            params = {"$skip": skip, "$count": count}

        result = self._request("GET", endpoint, params=params)
        return result.get("Data", [])

    def get_account_history(self, account_key: str | None = None, client_key: str | None = None, from_date: str | None = None, to_date: str | None = None) -> list[dict[str, Any]]:
        """Get account transaction history (trades, deposits, dividends, etc)."""
        params = {}
        if from_date:
            params["FromDate"] = from_date
        if to_date:
            params["ToDate"] = to_date

        # Use transactions endpoint
        if account_key:
            params["AccountKeys"] = account_key
        if client_key:
            params["ClientKey"] = client_key

        endpoint = "hist/v1/transactions"

        result = self._request("GET", endpoint, params=params)
        return result.get("Data", [])
