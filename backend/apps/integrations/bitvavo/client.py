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

DEFAULT_ACCESS_WINDOW_MS = 10_000


class BitvavoAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BitvavoClient:
    """Bitvavo REST API v2 client met HMAC-authenticatie (zelfde signing als officiële SDK)."""

    def __init__(self, api_key: str, api_secret: str, base_url: str | None = None):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.base_url = (base_url or settings.BITVAVO_API_URL).rstrip("/")
        self.access_window = int(
            getattr(settings, "BITVAVO_ACCESS_WINDOW", DEFAULT_ACCESS_WINDOW_MS)
        )

    @staticmethod
    def build_signing_path(path: str, query: str = "") -> str:
        """timestamp + method + '/v2' + endpoint + query + body (SDK-formaat)."""
        endpoint = "/" + path.lstrip("/")
        return f"/v2{endpoint}{query}"

    def _sign(self, timestamp: int, method: str, signing_path: str, body: str = "") -> str:
        payload = f"{timestamp}{method}{signing_path}{body}"
        return hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

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

        signing_path = self.build_signing_path(path, query)
        url = f"{self.base_url}/{path.lstrip('/')}{query}"

        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(",", ":"))

        timestamp = int(time.time() * 1000)
        signature = self._sign(timestamp, method.upper(), signing_path, body_str)

        headers = {
            "Bitvavo-Access-Key": self.api_key,
            "Bitvavo-Access-Signature": signature,
            "Bitvavo-Access-Timestamp": str(timestamp),
            "Bitvavo-Access-Window": str(self.access_window),
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

    def get_account_history(
        self,
        *,
        from_date_ms: int | None = None,
        to_date_ms: int | None = None,
        max_items: int = 100,
    ) -> list[dict]:
        """GET /account/history — alle transactietypes (gepagineerd)."""
        all_items: list[dict] = []
        page = 1
        total_pages = 1

        while page <= total_pages:
            params: dict = {"page": page, "maxItems": max_items}
            if from_date_ms is not None:
                params["fromDate"] = from_date_ms
            if to_date_ms is not None:
                params["toDate"] = to_date_ms

            data = self._request("GET", "account/history", params=params)
            if not isinstance(data, dict):
                break

            items = data.get("items") or []
            if isinstance(items, list):
                all_items.extend(items)

            total_pages = int(data.get("totalPages") or 1)
            page += 1

        return all_items

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
