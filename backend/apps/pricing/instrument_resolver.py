"""
Symbol/ISIN → Yahoo Finance ticker (platform-onafhankelijk).

Laag 1: korte tickers (aliases)
Laag 2: database InstrumentMapping
Laag 3: seed JSON
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

from apps.pricing.isin import looks_like_isin

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent / "data" / "euronext_isin_tickers.json"

SYMBOL_ALIASES: dict[str, str] = {
    "IWDA": "IWDA.AS",
    "IWDA.L": "IWDA.AS",
    "ASML": "ASML.AS",
    "SHELL": "SHELL.AS",
    "INGA": "INGA.AS",
    "VWCE": "VWCE.AS",
    "VUSA": "VUSA.AS",
}


@lru_cache(maxsize=1)
def _seed_map() -> dict[str, str]:
    try:
        raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Seed ISIN-map niet geladen: %s", exc)
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).upper(): str(v) for k, v in raw.items()}


def _db_ticker(isin: str) -> str | None:
    from apps.pricing.models import InstrumentMapping

    row = InstrumentMapping.objects.filter(isin=isin.upper()).first()
    return row.yahoo_ticker if row else None


def resolve_yahoo_ticker(symbol: str) -> str:
    upper = symbol.upper().strip()
    if upper in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[upper]
    if looks_like_isin(upper):
        mapped = _db_ticker(upper) or _seed_map().get(upper)
        return mapped if mapped else upper
    return upper


def list_unmapped_isins(symbols: list[str]) -> list[str]:
    from apps.pricing.services.instrument_service import list_unmapped_isins as _list

    return _list(symbols)
