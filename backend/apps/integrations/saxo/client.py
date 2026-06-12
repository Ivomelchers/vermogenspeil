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
            refresh_token: OAuth2 refresh token (optional, for token refresh)
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

    def refresh_access_token(self) -> tuple[str, str] | None:
        """Refresh OAuth access token using refresh token. Returns (new_access_token, new_refresh_token) or None if refresh fails."""
        if not self.refresh_token:
            return None

        from django.conf import settings

        token_endpoint = "https://sim.logonvalidation.net/token"
        client_id = getattr(settings, "SAXO_CLIENT_ID", "")
        client_secret = getattr(settings, "SAXO_CLIENT_SECRET", "")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            response = requests.post(token_endpoint, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()

            new_access_token = result.get("access_token")
            new_refresh_token = result.get("refresh_token", self.refresh_token)

            if new_access_token:
                # Update client with new tokens
                self.access_token = new_access_token
                self.refresh_token = new_refresh_token
                self.session.headers.update({"Authorization": f"Bearer {new_access_token}"})
                return (new_access_token, new_refresh_token)

            return None
        except requests.exceptions.RequestException:
            return None

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
        """Get open positions with full details (DisplayAndFormat, PositionBase, PositionView)."""
        endpoint = "port/v1/positions"
        params = {}

        # Use ClientKey if available (works for all accounts of a client)
        if client_key:
            params["ClientKey"] = client_key
        elif account_key:
            params["AccountKey"] = account_key

        # Try with fieldGroups first (lowercase - Saxo is case-sensitive!), fall back without if empty
        params_with_fields = {**params, "fieldGroups": "DisplayAndFormat,PositionBase,PositionView"}
        result = self._request("GET", endpoint, params=params_with_fields)
        data = result.get("Data", [])

        # If no data with fieldGroups, try without
        if not data:
            print(f"🔍 [SAXO API] No positions with fieldGroups, trying without...")
            result = self._request("GET", endpoint, params=params)
            data = result.get("Data", [])

        print(f"🔍 [SAXO API] get_positions response: {len(data)} positions")
        return data

    def get_trades(self, account_key: str | None = None, client_key: str | None = None, skip: int = 0, count: int = 100) -> list[dict[str, Any]]:
        """Get executed trades via reports API."""
        params = {"$skip": skip, "$top": count, "fieldGroups": "DisplayAndFormat"}

        # Use reports endpoint (most reliable)
        if client_key:
            endpoint = f"cs/v1/reports/trades/{client_key}"
        elif account_key:
            # Fallback: try the direct trades endpoint
            endpoint = f"trade/v2/trades/{account_key}"
            params = {"$skip": skip, "$count": count, "fieldGroups": "DisplayAndFormat"}
        else:
            # Try /me variant
            endpoint = "trade/v2/trades/me"
            params = {"$skip": skip, "$count": count, "fieldGroups": "DisplayAndFormat"}

        result = self._request("GET", endpoint, params=params)
        data = result.get("Data", [])

        # Debug: check if DisplayAndFormat is in the response
        if data:
            print(f"🔍 [SAXO API] get_trades response has keys: {list(data[0].keys())}")
            if "DisplayAndFormat" in data[0]:
                print(f"  ✅ DisplayAndFormat found in trade response")
            else:
                print(f"  ❌ DisplayAndFormat NOT in trade response - endpoint doesn't support it")

        return data

    def get_account_history(self, account_key: str | None = None, client_key: str | None = None, from_date: str | None = None, to_date: str | None = None) -> list[dict[str, Any]]:
        """Get account transaction history (trades, deposits, dividends, etc)."""
        params = {}
        if from_date:
            params["FromDate"] = from_date
        if to_date:
            params["ToDate"] = to_date

        endpoint = "hist/v1/transactions"

        # The hist/v1/transactions endpoint returns authenticated user's transactions
        # It doesn't support ClientKey parameter - just call without it
        result = self._request("GET", endpoint, params=params)
        return result.get("Data", [])

    def get_orders(self) -> list[dict[str, Any]]:
        """Get pending/open orders for authenticated user. Returns all orders regardless of account."""
        params = {"fieldGroups": "DisplayAndFormat"}
        endpoint = "port/v1/orders/me"
        result = self._request("GET", endpoint, params=params)
        return result.get("Data", [])
