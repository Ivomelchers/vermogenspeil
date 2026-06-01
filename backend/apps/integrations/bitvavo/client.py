import hashlib
import hmac
import json
import logging
import time
from decimal import Decimal
from urllib.parse import urlencode

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class BitvavoAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BitvavoClient:
    """Bitvavo REST API v2 client met HMAC-authenticatie."""

    def __init__(self, api_key: str, api_secret: str, base_url: str | None = None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = (base_url or settings.BITVAVO_API_URL).rstrip("/")

    def _sign(self, timestamp: int, method: str, path: str, body: str = "") -> str:
        payload = f"{timestamp}{method}{path}{body}"
        return hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def _signing_path(self, path: str) -> str:
        normalized = path.lstrip("/")
        base = self.base_url.rstrip("/")
        if base.endswith("/v2"):
            return f"/v2/{normalized}"
        return f"/{normalized}"

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict | None = None,
        body: dict | None = None,
    ) -> list | dict:
        query = ""
        if params:
            query = "?" + urlencode(params)
        resource_path = self._signing_path(path)
        url = f"{self.base_url}/{path.lstrip('/')}{query}"
        body_str = json.dumps(body) if body else ""
        timestamp = int(time.time() * 1000)
        signature = self._sign(timestamp, method.upper(), resource_path, body_str)

        headers = {
            "BITVAVO-ACCESS-KEY": self.api_key,
            "BITVAVO-ACCESS-SIGNATURE": signature,
            "BITVAVO-ACCESS-TIMESTAMP": str(timestamp),
            "Content-Type": "application/json",
        }

        try:
            response = requests.request(
                method.upper(),
                url,
                headers=headers,
                data=body_str or None,
                timeout=30,
            )
        except requests.RequestException as exc:
            logger.exception("Bitvavo request failed")
            raise BitvavoAPIError("Kon Bitvavo niet bereiken.") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("error", response.text)
            except (ValueError, AttributeError):
                detail = response.text
            raise BitvavoAPIError(
                f"Bitvavo API-fout: {detail}",
                status_code=response.status_code,
            )

        if not response.text:
            return []

        return response.json()

    def get_balance(self) -> list[dict]:
        data = self._request("GET", "balance")
        return data if isinstance(data, list) else []

    def get_trades(self, market: str, *, limit: int = 500) -> list[dict]:
        data = self._request(
            "GET",
            "trades",
            params={"market": market, "limit": limit},
        )
        return data if isinstance(data, list) else []

    def get_markets(self) -> list[dict]:
        data = self._request("GET", "markets")
        return data if isinstance(data, list) else []

    @staticmethod
    def parse_balance(entry: dict) -> tuple[str, Decimal] | None:
        symbol = entry.get("symbol", "")
        available = Decimal(str(entry.get("available", "0")))
        in_order = Decimal(str(entry.get("inOrder", "0")))
        quantity = available + in_order
        if quantity <= 0:
            return None
        return symbol, quantity

    @staticmethod
    def parse_trade(trade: dict, market: str) -> dict:
        base_symbol = market.split("-")[0] if "-" in market else market
        return {
            "external_id": trade.get("id", ""),
            "symbol": base_symbol,
            "side": trade.get("side", "buy"),
            "quantity": Decimal(str(trade.get("amount", "0"))),
            "price_eur": Decimal(str(trade.get("price", "0"))),
            "fee_eur": Decimal(str(trade.get("fee", "0"))),
            "occurred_at_ms": int(trade.get("timestamp", 0)),
            "market": market,
        }
