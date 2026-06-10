import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)

TRADING212_PRODUCTION_URL = "https://api.trading212.com/api/v0"
TRADING212_SANDBOX_URL = "https://sandbox.trading212.com/api/v0"


class Trading212APIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class Trading212Client:
    """Trading212 REST API v0 client met token-authenticatie."""

    def __init__(
        self,
        api_key: str,
        sandbox: bool = False,
        base_url: str | None = None,
    ):
        self.api_key = api_key.strip()
        if base_url is not None:
            self.base_url = base_url.rstrip("/")
        elif sandbox:
            self.base_url = TRADING212_SANDBOX_URL
        else:
            self.base_url = TRADING212_PRODUCTION_URL

    def _request(self, method: str, path: str, *, params: dict | None = None) -> dict | list:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method.upper(),
                url,
                headers=headers,
                params=params or None,
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.exception("Trading212 request failed")
            raise Trading212APIError("Kon Trading212 niet bereiken.") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("message", response.text)
            except (ValueError, AttributeError):
                detail = response.text
            raise Trading212APIError(
                f"Trading212 API-fout: {detail}",
                status_code=response.status_code,
            )

        return response.json() if response.text else {}

    def fetch_portfolio(self) -> list[dict]:
        """GET /portfolio — geeft open posities terug."""
        data = self._request("GET", "/portfolio")
        if isinstance(data, dict):
            return data.get("positions") or []
        return []

    def fetch_order_history(self, limit: int = 50) -> list[dict]:
        """GET /history/orders — geeft uitgevoerde orders terug."""
        data = self._request("GET", "/history/orders", params={"limit": limit})
        if isinstance(data, dict):
            return data.get("items") or []
        return []

    def fetch_account_cash(self) -> dict:
        """GET /accounts/cash — geeft cash-saldo terug."""
        data = self._request("GET", "/accounts/cash")
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def parse_position(entry: dict) -> tuple[str, Decimal] | None:
        ticker = (entry.get("ticker") or "").strip()
        if not ticker:
            return None
        quantity = Decimal(str(entry.get("quantity") or "0"))
        if quantity <= 0:
            return None
        return ticker, quantity
