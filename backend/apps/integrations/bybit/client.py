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

DEFAULT_RECV_WINDOW_MS = 5_000


class BybitAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class BybitClient:
    """Bybit REST API v5 client met HMAC-authenticatie."""

    def __init__(self, api_key: str, api_secret: str, base_url: str | None = None):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.base_url = (base_url or settings.BYBIT_API_URL).rstrip("/")
        self.recv_window = int(getattr(settings, "BYBIT_RECV_WINDOW", DEFAULT_RECV_WINDOW_MS))

    def _sign(self, timestamp: int, query_string: str) -> str:
        payload = f"{timestamp}{self.api_key}{self.recv_window}{query_string}"
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
    ) -> dict:
        query_string = urlencode(params) if params else ""
        url = f"{self.base_url}/{path.lstrip('/')}"
        if query_string:
            url = f"{url}?{query_string}"

        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(",", ":"))

        timestamp = int(time.time() * 1000)
        signature = self._sign(timestamp, query_string)

        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-TIMESTAMP": str(timestamp),
            "X-BAPI-RECV-WINDOW": str(self.recv_window),
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
            logger.exception("Bybit request failed")
            raise BybitAPIError("Kon Bybit niet bereiken.") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("retMsg", response.text)
            except (ValueError, AttributeError):
                detail = response.text
            raise BybitAPIError(
                f"Bybit API-fout: {detail}",
                status_code=response.status_code,
            )

        data = response.json() if response.text else {}
        ret_code = data.get("retCode", 0)
        if ret_code != 0:
            raise BybitAPIError(
                f"Bybit API-fout: {data.get('retMsg', ret_code)}",
                status_code=response.status_code,
            )

        return data.get("result") or {}

    def get_wallet_balance(self, *, account_type: str = "UNIFIED") -> list[dict]:
        result = self._request(
            "GET",
            "v5/account/wallet-balance",
            params={"accountType": account_type},
        )
        coins: list[dict] = []
        for account in result.get("list") or []:
            if not isinstance(account, dict):
                continue
            for coin in account.get("coin") or []:
                if isinstance(coin, dict):
                    coins.append(coin)
        return coins

    def get_spot_executions(
        self,
        *,
        limit: int = 100,
        since_ms: int | None = None,
    ) -> list[dict]:
        """GET /v5/execution/list — spot fills (gepagineerd via cursor)."""
        all_items: list[dict] = []
        cursor = ""

        while True:
            params: dict = {"category": "spot", "limit": limit}
            if cursor:
                params["cursor"] = cursor
            if since_ms is not None:
                params["startTime"] = since_ms

            result = self._request("GET", "v5/execution/list", params=params)
            items = result.get("list") or []
            if isinstance(items, list):
                all_items.extend(items)

            cursor = result.get("nextPageCursor") or ""
            if not cursor or not items:
                break

        return all_items

    @staticmethod
    def parse_balance(entry: dict) -> tuple[str, Decimal] | None:
        symbol = (entry.get("coin") or "").strip()
        if not symbol:
            return None
        wallet = Decimal(str(entry.get("walletBalance") or entry.get("equity") or "0"))
        if wallet <= 0:
            return None
        return symbol, wallet
