"""
Dynamic symbol discovery from price providers.

Instead of hardcoding symbols, fetch all available symbols from APIs
and cache them. This automatically supports meme coins, new coins, etc.

Rate limiting strategy:
- Run once/day @ 2 AM (1 API call per provider per day)
- Cache for 24 hours (no repeat calls within window)
- Exponential backoff on failures
- Handle 429 (Too Many Requests) responses gracefully
"""

import logging
import time
from datetime import timedelta
from decimal import Decimal

import requests
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

CACHE_TTL = 86400  # 24 hours (1 call per day max)
DISCOVERY_LOCK_KEY = "symbol_discovery:running"  # Prevent concurrent refreshes
DISCOVERY_LOCK_TTL = 300  # 5 min - if lock held longer, something is wrong
CACHE_KEYS = {
    "crypto_bitvavo": "symbol_discovery:crypto:bitvavo",
    "crypto_coingecko": "symbol_discovery:crypto:coingecko",
    "stocks_yahoo": "symbol_discovery:stocks:yahoo",
}


class SymbolDiscoveryService:
    """Fetch and cache all available symbols from providers."""

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout
        self.max_retries = 3
        self.initial_retry_delay = 5  # seconds

    def get_crypto_symbols(self) -> set[str]:
        """Get all crypto symbols from all providers."""
        symbols = set()

        # Bitvavo markets
        bitvavo_symbols = self._fetch_bitvavo_symbols()
        symbols.update(bitvavo_symbols)

        # CoinGecko coins
        coingecko_symbols = self._fetch_coingecko_symbols()
        symbols.update(coingecko_symbols)

        return symbols

    def get_stock_symbols(self) -> set[str]:
        """Get all stock symbols from providers."""
        # Yahoo Finance doesn't expose a public API for all symbols
        # Use popular stocks + cached list
        return self._get_popular_stocks()

    def _fetch_bitvavo_symbols(self) -> set[str]:
        """
        Fetch crypto symbols from Bitvavo markets API.

        Uses exponential backoff on rate limiting (429).
        Returns cached result if available.
        """
        cached = cache.get(CACHE_KEYS["crypto_bitvavo"])
        if cached is not None:
            logger.info("Bitvavo symbols from cache")
            return set(cached)

        try:
            from django.conf import settings

            url = f"{settings.BITVAVO_API_URL}/markets"

            # Exponential backoff on rate limit
            for attempt in range(self.max_retries):
                try:
                    response = requests.get(url, timeout=self.timeout)

                    # Handle rate limiting
                    if response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            delay = self.initial_retry_delay * (2 ** attempt)
                            logger.warning(
                                f"Bitvavo rate limited. Retry in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            logger.error("Bitvavo rate limit exceeded after retries")
                            return set()

                    response.raise_for_status()
                    break

                except requests.Timeout:
                    if attempt < self.max_retries - 1:
                        delay = self.initial_retry_delay * (2 ** attempt)
                        logger.warning(f"Bitvavo timeout. Retry in {delay}s")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error("Bitvavo timeout after retries")
                        return set()

            markets = response.json()
            if not isinstance(markets, list):
                logger.warning("Bitvavo markets response not a list")
                return set()

            symbols = set()
            for market in markets:
                if not isinstance(market, dict):
                    continue
                market_id = market.get("id", "")  # e.g., "BTC-EUR"
                if "-EUR" in market_id:
                    symbol = market_id.split("-")[0]
                    symbols.add(symbol)

            cache.set(CACHE_KEYS["crypto_bitvavo"], list(symbols), CACHE_TTL)
            logger.info(f"Discovered {len(symbols)} crypto symbols on Bitvavo")
            return symbols

        except (requests.RequestException, ValueError) as e:
            logger.exception(f"Failed to fetch Bitvavo symbols: {e}")
            return set()

    def _fetch_coingecko_symbols(self) -> set[str]:
        """
        Fetch crypto symbols from CoinGecko coins list.

        Uses exponential backoff on rate limiting (429).
        """
        cached = cache.get(CACHE_KEYS["crypto_coingecko"])
        if cached is not None:
            logger.info("CoinGecko symbols from cache")
            return set(cached)

        try:
            url = "https://api.coingecko.com/api/v3/coins/list"

            # Exponential backoff on rate limit
            for attempt in range(self.max_retries):
                try:
                    response = requests.get(url, timeout=self.timeout)

                    # Handle rate limiting
                    if response.status_code == 429:
                        if attempt < self.max_retries - 1:
                            delay = self.initial_retry_delay * (2 ** attempt)
                            logger.warning(
                                f"CoinGecko rate limited. Retry in {delay}s (attempt {attempt + 1}/{self.max_retries})"
                            )
                            time.sleep(delay)
                            continue
                        else:
                            logger.error("CoinGecko rate limit exceeded after retries")
                            return set()

                    response.raise_for_status()
                    break

                except requests.Timeout:
                    if attempt < self.max_retries - 1:
                        delay = self.initial_retry_delay * (2 ** attempt)
                        logger.warning(f"CoinGecko timeout. Retry in {delay}s")
                        time.sleep(delay)
                        continue
                    else:
                        logger.error("CoinGecko timeout after retries")
                        return set()

            coins = response.json()
            if not isinstance(coins, list):
                logger.warning("CoinGecko coins response not a list")
                return set()

            symbols = set()
            for coin in coins:
                if not isinstance(coin, dict):
                    continue
                symbol = (coin.get("symbol") or "").upper().strip()
                if symbol and len(symbol) <= 10:  # Filter out weird symbols
                    symbols.add(symbol)

            cache.set(CACHE_KEYS["crypto_coingecko"], list(symbols), CACHE_TTL)
            logger.info(f"Discovered {len(symbols)} crypto symbols on CoinGecko")
            return symbols

        except (requests.RequestException, ValueError) as e:
            logger.exception(f"Failed to fetch CoinGecko symbols: {e}")
            return set()

    def _get_popular_stocks(self) -> set[str]:
        """Return popular stocks (Yahoo Finance doesn't expose all symbols)."""
        # Popular stocks - can be extended
        return frozenset({
            # US Tech
            "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
            # US Banks
            "JPM", "BAC", "WFC", "GS", "MS",
            # EU Stocks
            "ASML", "ADYEN", "PROSUS", "SAP", "SIEMENS", "MERCEDES",
            # Netherlands
            "SHELL", "UNILEVER", "ING", "ABN", "NN",
        })

    def refresh_all(self) -> dict[str, int]:
        """
        Refresh all symbol caches. Prevents concurrent refreshes via distributed lock.

        Returns cache hit status and symbol counts.
        """
        # Distributed lock: prevent multiple workers from calling APIs simultaneously
        lock_acquired = cache.add(DISCOVERY_LOCK_KEY, "locked", DISCOVERY_LOCK_TTL)
        if not lock_acquired:
            logger.warning(
                "Symbol discovery already running (lock exists). Skipping refresh."
            )
            return {
                "crypto_total": 0,
                "stocks_total": 0,
                "status": "skipped_lock",
            }

        try:
            results = {}

            crypto = self.get_crypto_symbols()
            results["crypto_total"] = len(crypto)
            logger.info(f"Refreshed crypto symbols: {len(crypto)} total")

            stocks = self.get_stock_symbols()
            results["stocks_total"] = len(stocks)
            logger.info(f"Refreshed stock symbols: {len(stocks)} total")

            results["status"] = "success"
            return results

        finally:
            # Always release lock
            cache.delete(DISCOVERY_LOCK_KEY)


def get_symbol_discovery_service() -> SymbolDiscoveryService:
    """Get singleton symbol discovery service."""
    return SymbolDiscoveryService()
