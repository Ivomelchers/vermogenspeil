def live_price_cache_key(symbol: str, asset_type: str) -> str:
    return f"pricing:live:{asset_type}:{symbol.upper()}"


def historical_price_cache_key(symbol: str, asset_type: str, on_date: str) -> str:
    return f"pricing:hist:{asset_type}:{symbol.upper()}:{on_date}"
