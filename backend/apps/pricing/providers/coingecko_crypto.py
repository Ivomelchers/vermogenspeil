"""CoinGecko live crypto — dynamic symbol discovery, no hardcoded list."""

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings
from django.core.cache import cache

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.base import LivePriceQuote

logger = logging.getLogger(__name__)

CRYPTO_ASSET_TYPES = frozenset({AssetType.CRYPTO})
SYMBOL_CACHE_KEY = "coingecko:symbol_map"
SYMBOL_CACHE_TTL = 86400 * 7  # 7 days — update weekly if new coins appear
NOT_FOUND_MARKER = "__NOT_FOUND__"


class CoinGeckoCryptoProvider:
    """
    Dynamic symbol discovery via CoinGecko.

    No hardcoded coin list. When a symbol is encountered:
    1. Check local cache (symbol → coin_id)
    2. Query CoinGecko /search endpoint if not cached
    3. Cache the result for 7 days
    4. Fetch prices in bulk

    Supports any coin on CoinGecko automatically.
    """

    asset_types = CRYPTO_ASSET_TYPES

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.base_url = "https://api.coingecko.com/api/v3"

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def _headers(self) -> dict[str, str]:
        key = getattr(settings, "COINGECKO_API_KEY", "") or ""
        if key:
            return {"x-cg-demo-api-key": key}
        return {}

    def _search_coin_id(self, symbol: str) -> str | None:
        """
        Search CoinGecko for a coin ID by symbol.
        Returns coin_id (e.g., "bitcoin") or None if not found.
        """
        try:
            response = requests.get(
                f"{self.base_url}/search",
                params={"query": symbol},
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()

            coins = data.get("coins", [])
            for coin in coins:
                if coin.get("symbol", "").upper() == symbol.upper():
                    return coin.get("id")

            logger.debug(f"CoinGecko: '{symbol}' niet gevonden")
            return None

        except (requests.RequestException, ValueError) as exc:
            logger.warning(f"CoinGecko search voor '{symbol}' mislukt: {exc}")
            return None

    def _resolve_coin_id(self, symbol: str) -> str | None:
        """
        Resolve symbol → coin_id with caching.

        1. Load cache
        2. If symbol in cache, return (or NOT_FOUND_MARKER)
        3. If not in cache, search and cache result
        4. Return coin_id or None
        """
        symbol = symbol.upper().strip()
        if not symbol:
            return None

        symbol_map: dict[str, str] = cache.get(SYMBOL_CACHE_KEY) or {}

        if symbol in symbol_map:
            coin_id = symbol_map[symbol]
            if coin_id == NOT_FOUND_MARKER:
                return None
            return coin_id

        coin_id = self._search_coin_id(symbol)

        symbol_map[symbol] = coin_id or NOT_FOUND_MARKER
        cache.set(SYMBOL_CACHE_KEY, symbol_map, SYMBOL_CACHE_TTL)

        return coin_id

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        """
        Fetch live prices for symbols by resolving each to a coin_id,
        then querying CoinGecko in one batch.
        """
        coin_map: dict[str, str] = {}
        for symbol in symbols:
            upper = symbol.upper().strip()
            if not upper:
                continue

            coin_id = self._resolve_coin_id(upper)
            if coin_id and coin_id not in coin_map:
                coin_map[coin_id] = upper

        if not coin_map:
            return {}

        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    "ids": ",".join(coin_map.keys()),
                    "vs_currencies": "eur",
                },
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("CoinGecko live prices mislukt: %s", exc)
            raise PriceFetchError("CoinGecko niet beschikbaar") from exc

        if not isinstance(payload, dict):
            return {}

        quotes: dict[str, LivePriceQuote] = {}
        for coin_id, portfolio_symbol in coin_map.items():
            entry = payload.get(coin_id)
            if not isinstance(entry, dict):
                continue
            eur = entry.get("eur")
            if eur is None:
                continue
            try:
                price = Decimal(str(eur))
            except (InvalidOperation, TypeError):
                continue
            if price <= 0:
                continue
            quotes[portfolio_symbol] = LivePriceQuote(
                symbol=portfolio_symbol,
                price_eur=price,
                source="coingecko",
            )

        if not quotes:
            raise PriceFetchError("CoinGecko: geen EUR-koersen in response")

        return quotes
