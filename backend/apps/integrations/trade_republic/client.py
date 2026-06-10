import logging
from decimal import Decimal

import requests

logger = logging.getLogger(__name__)

TRADE_REPUBLIC_PRODUCTION_URL = "https://api.traderepublic.com/api/v1"


class TradeRepublicAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class TradeRepublicClient:
    """Trade Republic REST API v1 client met Bearer-token authenticatie."""

    def __init__(
        self,
        api_key: str,
        base_url: str | None = None,
    ):
        self.api_key = api_key.strip()
        self.base_url = (base_url.rstrip("/") if base_url is not None else TRADE_REPUBLIC_PRODUCTION_URL)

    def _request(self, method: str, path: str, *, params: dict | None = None) -> dict | list:
        url = f"{self.base_url}/{path.lstrip('/')}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
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
            logger.exception("Trade Republic request failed")
            raise TradeRepublicAPIError("Kon Trade Republic niet bereiken.") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("message", response.text)
            except (ValueError, AttributeError):
                detail = response.text
            raise TradeRepublicAPIError(
                f"Trade Republic API-fout: {detail}",
                status_code=response.status_code,
            )

        return response.json() if response.text else {}

    def fetch_holdings(self) -> dict:
        """GET /portfolio/holdings — geeft open posities terug."""
        data = self._request("GET", "/portfolio/holdings")
        if isinstance(data, dict):
            return data
        return {}

    def fetch_activities(self, limit: int = 50) -> dict:
        """GET /timeline/activities — geeft activiteiten/transacties terug."""
        data = self._request("GET", "/timeline/activities", params={"limit": limit})
        if isinstance(data, dict):
            return data
        return {}

    @staticmethod
    def parse_holding(entry: dict) -> tuple[str, str, Decimal] | None:
        """Parseer een holding-entry naar (isin, name, quantity) of None."""
        isin = (entry.get("isin") or "").strip()
        if not isin:
            return None
        quantity = Decimal(str(entry.get("quantity") or "0"))
        if quantity <= 0:
            return None
        name = (entry.get("name") or isin).strip()
        return isin, name, quantity
