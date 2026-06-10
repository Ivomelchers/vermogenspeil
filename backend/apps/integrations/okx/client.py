import base64
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


class OkxAPIError(Exception):
    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class OkxClient:
    """OKX REST API v5 client met HMAC-authenticatie (base64 sign)."""

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str,
        base_url: str | None = None,
    ):
        self.api_key = api_key.strip()
        self.api_secret = api_secret.strip()
        self.passphrase = passphrase.strip()
        self.base_url = (base_url or settings.OKX_API_URL).rstrip("/")

    def _sign(self, timestamp: str, method: str, request_path: str, body: str = "") -> str:
        payload = f"{timestamp}{method.upper()}{request_path}{body}"
        digest = hmac.new(
            self.api_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        return base64.b64encode(digest).decode("utf-8")

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

        request_path = f"/{path.lstrip('/')}{query}"
        url = f"{self.base_url}{request_path}"

        body_str = ""
        if body:
            body_str = json.dumps(body, separators=(",", ":"))

        timestamp = str(time.time())
        signature = self._sign(timestamp, method, request_path, body_str)

        headers = {
            "OK-ACCESS-KEY": self.api_key,
            "OK-ACCESS-SIGN": signature,
            "OK-ACCESS-TIMESTAMP": timestamp,
            "OK-ACCESS-PASSPHRASE": self.passphrase,
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
            logger.exception("OKX request failed")
            raise OkxAPIError("Kon OKX niet bereiken.") from exc

        if response.status_code >= 400:
            try:
                detail = response.json().get("msg", response.text)
            except (ValueError, AttributeError):
                detail = response.text
            raise OkxAPIError(
                f"OKX API-fout: {detail}",
                status_code=response.status_code,
            )

        data = response.json() if response.text else {}
        code = str(data.get("code", "0"))
        if code not in ("0", ""):
            raise OkxAPIError(
                f"OKX API-fout: {data.get('msg', code)}",
                status_code=response.status_code,
            )

        return data.get("data") or []

    def get_balance(self) -> list[dict]:
        data = self._request("GET", "api/v5/account/balance")
        details: list[dict] = []
        if isinstance(data, list):
            for account in data:
                if not isinstance(account, dict):
                    continue
                for detail in account.get("details") or []:
                    if isinstance(detail, dict):
                        details.append(detail)
        return details

    def get_spot_fills(
        self,
        *,
        limit: int = 100,
        since_ms: int | None = None,
    ) -> list[dict]:
        """GET /api/v5/trade/fills-history — spot fills (gepagineerd)."""
        all_items: list[dict] = []
        after = ""

        while True:
            params: dict = {"instType": "SPOT", "limit": str(limit)}
            if after:
                params["after"] = after
            if since_ms is not None:
                params["begin"] = str(since_ms)

            batch = self._request("GET", "api/v5/trade/fills-history", params=params)
            if not isinstance(batch, list) or not batch:
                break

            all_items.extend(batch)

            if len(batch) < limit:
                break

            last_id = batch[-1].get("tradeId") or batch[-1].get("billId")
            if not last_id:
                break
            after = str(last_id)

        return all_items

    @staticmethod
    def parse_balance(entry: dict) -> tuple[str, Decimal] | None:
        symbol = (entry.get("ccy") or "").strip()
        if not symbol:
            return None
        cash = Decimal(str(entry.get("cashBal") or entry.get("availBal") or "0"))
        if cash <= 0:
            return None
        return symbol, cash
