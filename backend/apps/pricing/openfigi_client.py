"""OpenFIGI: gratis ISIN → exchange-ticker lookup (Bloomberg)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import requests
from django.conf import settings

from apps.portfolio.models import AssetType
from apps.pricing.mic_suffix import build_yahoo_ticker

logger = logging.getLogger(__name__)

OPENFIGI_URL = "https://api.openfigi.com/v3/mapping"
REQUEST_TIMEOUT = 8


@dataclass(frozen=True)
class OpenFigiMatch:
    yahoo_ticker: str
    mic: str
    exch_code: str
    security_type: str
    asset_type: str


def openfigi_enabled() -> bool:
    return getattr(settings, "OPENFIGI_ENABLED", True)


def _map_security_type(security_type: str) -> str:
    lower = (security_type or "").lower()
    if "etf" in lower:
        return AssetType.ETF
    if "fund" in lower or "mutual" in lower:
        return AssetType.FUND
    if "stock" in lower or "equity" in lower or "common" in lower:
        return AssetType.STOCK
    return ""


def fetch_isin_match(isin: str, *, mic_hint: str = "") -> OpenFigiMatch | None:
    if not openfigi_enabled():
        return None

    isin_upper = isin.upper().strip()
    if len(isin_upper) != 12:
        return None

    headers = {"Content-Type": "application/json"}
    api_key = getattr(settings, "OPENFIGI_API_KEY", "") or ""
    if api_key:
        headers["X-OPENFIGI-APIKEY"] = api_key

    try:
        response = requests.post(
            OPENFIGI_URL,
            json=[{"idType": "ID_ISIN", "idValue": isin_upper}],
            headers=headers,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        body = response.json()
    except (requests.RequestException, ValueError) as exc:
        logger.warning("OpenFIGI mislukt voor %s: %s", isin_upper, exc)
        return None

    if not isinstance(body, list) or not body:
        return None
    entry = body[0]
    if not isinstance(entry, dict) or entry.get("error"):
        return None
    data = entry.get("data")
    if not isinstance(data, list) or not data:
        return None

    best = _pick_best_row(data, mic_hint=mic_hint)
    if not best:
        return None
    ticker = (best.get("ticker") or "").strip()
    if not ticker:
        return None

    exch = (best.get("exchCode") or "").strip()
    mic = (best.get("mic") or mic_hint or "").strip()
    security_type = (best.get("securityType") or "").strip()
    yahoo = build_yahoo_ticker(ticker=ticker, exch_code=exch, mic=mic)
    if not yahoo:
        return None

    return OpenFigiMatch(
        yahoo_ticker=yahoo,
        mic=mic,
        exch_code=exch,
        security_type=security_type,
        asset_type=_map_security_type(security_type),
    )


def _pick_best_row(rows: list[dict], *, mic_hint: str) -> dict | None:
    mic_upper = (mic_hint or "").upper()
    candidates = [
        r
        for r in rows
        if isinstance(r, dict)
        and (not r.get("marketSector") or (r.get("marketSector") or "").lower() in (
            "equity",
            "etf",
            "mutual fund",
            "fund",
        ))
    ]
    if not candidates:
        candidates = [r for r in rows if isinstance(r, dict)]
    if mic_upper:
        for row in candidates:
            if (row.get("mic") or "").upper() == mic_upper:
                return row
    return candidates[0] if candidates else None
