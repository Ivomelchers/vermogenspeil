"""
Symbol/ISIN → Yahoo Finance ticker.

Data in `data/euronext_isin_tickers.json` (uitbreidbaar zonder code-wijziging).
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_PATH = Path(__file__).resolve().parent / "data" / "euronext_isin_tickers.json"

# Korte tickers (handmatig / demo) — geen ISIN
SYMBOL_ALIASES: dict[str, str] = {
    "IWDA": "IWDA.AS",
    "IWDA.L": "IWDA.AS",
    "ASML": "ASML.AS",
    "SHELL": "SHELL.AS",
    "INGA": "INGA.AS",
    "VWCE": "VWCE.AS",
    "VUSA": "VUSA.AS",
}


def looks_like_isin(symbol: str) -> bool:
    upper = symbol.upper().strip()
    return len(upper) == 12 and upper[:2].isalpha() and upper[2:].isalnum()


@lru_cache(maxsize=1)
def _isin_ticker_map() -> dict[str, str]:
    try:
        raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("ISIN-ticker map niet geladen: %s", exc)
        return {}
    if not isinstance(raw, dict):
        return {}
    return {str(k).upper(): str(v) for k, v in raw.items()}


def resolve_yahoo_ticker(symbol: str) -> str:
    """
    Portfolio-symbol (ISIN of ticker) → Yahoo-ticker (meestal Euronext .AS).
    Onbekende ISIN: retourneert ISIN zelf (Yahoo faalt → kostprijs-fallback).
    """
    upper = symbol.upper().strip()
    if upper in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[upper]
    if looks_like_isin(upper):
        return _isin_ticker_map().get(upper, upper)
    return upper


def list_unmapped_isins(symbols: list[str]) -> list[str]:
    """ISINs zonder entry in de map (voor logging / onderhoud)."""
    known = _isin_ticker_map()
    return [s.upper() for s in symbols if looks_like_isin(s) and s.upper() not in known]
