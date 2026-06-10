"""
Symbol validation: supports dynamic symbol discovery from price providers.

Instead of hardcoding symbols, we fetch them from provider APIs and cache:
- Bitvavo markets API (/v2/markets) → all EUR pairs
- CoinGecko coins API (/v3/coins/list) → all coins
- Yahoo Finance → popular stocks (API limited)

New symbols (meme coins, new listings) are automatically supported within 24h.
"""

import logging
from django.core.cache import cache

from apps.portfolio.models import AssetType

logger = logging.getLogger(__name__)

# Cache keys for dynamic symbol discovery
CACHE_KEYS = {
    "crypto": "symbol_discovery:crypto",  # All crypto symbols
    "stocks": "symbol_discovery:stocks",  # All stock symbols
}

# Fallback lists if cache is empty (first run before discovery runs)
FALLBACK_CRYPTO_SYMBOLS = frozenset({
    "BTC", "ETH", "SOL", "XRP", "ADA", "DOT", "LINK", "LTC", "AR",
})

FALLBACK_STOCK_SYMBOLS = frozenset({
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA",
    "ASML", "ADYEN", "PROSUS", "SAP", "SIEMENS",
})


def get_supported_symbols(asset_type: str) -> frozenset[str]:
    """
    Get all symbols available for this asset type.

    First checks cache (populated by periodic symbol discovery).
    Falls back to hardcoded list if cache empty (e.g., on first run).
    """
    if asset_type == AssetType.CRYPTO:
        cached = cache.get(CACHE_KEYS["crypto"])
        if cached:
            return frozenset(cached)
        return FALLBACK_CRYPTO_SYMBOLS

    elif asset_type == AssetType.STOCK:
        cached = cache.get(CACHE_KEYS["stocks"])
        if cached:
            return frozenset(cached)
        return FALLBACK_STOCK_SYMBOLS

    elif asset_type == AssetType.ETF:
        # ETFs use same provider as stocks
        cached = cache.get(CACHE_KEYS["stocks"])
        if cached:
            return frozenset(cached)
        return FALLBACK_STOCK_SYMBOLS

    return frozenset()


def is_symbol_supported(symbol: str, asset_type: str) -> bool:
    """Check if symbol is supported by any provider."""
    supported = get_supported_symbols(asset_type)
    return symbol.upper().strip() in supported


def suggest_similar_symbols(symbol: str, asset_type: str, max_suggestions: int = 3) -> list[str]:
    """Suggest similar symbols if the user typed something wrong."""
    from difflib import get_close_matches

    supported = get_supported_symbols(asset_type)
    upper_symbol = symbol.upper().strip()

    # First try close matches (for typos)
    matches = get_close_matches(upper_symbol, supported, n=max_suggestions, cutoff=0.6)

    # If no matches, try partial matches (prefix)
    if not matches:
        matches = [s for s in sorted(supported) if s.startswith(upper_symbol[:2])][:max_suggestions]

    return sorted(matches)
