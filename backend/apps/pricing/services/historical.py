import logging
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.core.cache import cache

from apps.portfolio.models import AssetType
from apps.pricing.services.cache_keys import historical_price_cache_key

logger = logging.getLogger(__name__)

AMSTERDAM = ZoneInfo("Europe/Amsterdam")

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}


def _cache_get(symbol: str, asset_type: str, on_date: date) -> Decimal | None:
    cached = cache.get(historical_price_cache_key(symbol, asset_type, on_date.isoformat()))
    if cached is None:
        return None
    return Decimal(str(cached["price_eur"]))


def _cache_set(symbol: str, asset_type: str, on_date: date, price: Decimal, source: str) -> None:
    from django.conf import settings

    ttl = getattr(settings, "PRICE_CACHE_TTL_HISTORICAL_SECONDS", 86400)
    cache.set(
        historical_price_cache_key(symbol, asset_type, on_date.isoformat()),
        {"price_eur": str(price), "source": source},
        timeout=ttl,
    )


def fetch_historical_price_eur(symbol: str, asset_type: str, on_date: date) -> Decimal | None:
    """Historische EUR-koers op een kalenderdag (Europe/Amsterdam)."""
    symbol = symbol.upper().strip()
    cached = _cache_get(symbol, asset_type, on_date)
    if cached is not None:
        return cached

    price: Decimal | None = None
    source = ""

    if asset_type == AssetType.CRYPTO:
        price, source = _fetch_coingecko_history(symbol, on_date)
    elif asset_type in (AssetType.STOCK, AssetType.ETF, AssetType.FUND):
        price, source = _fetch_yahoo_history(symbol, on_date)

    if price and price > 0:
        _cache_set(symbol, asset_type, on_date, price, source)
        return price
    return None


def _fetch_coingecko_history(symbol: str, on_date: date) -> tuple[Decimal | None, str]:
    coin_id = COINGECKO_IDS.get(symbol)
    if not coin_id:
        return None, ""

    try:
        import requests
    except ImportError:
        return None, ""

    date_str = on_date.strftime("%d-%m-%Y")
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history"
    try:
        response = requests.get(url, params={"date": date_str, "localization": "false"}, timeout=15)
        response.raise_for_status()
        payload = response.json()
        price_eur = payload.get("market_data", {}).get("current_price", {}).get("eur")
        if price_eur is None:
            return None, ""
        return Decimal(str(price_eur)), "coingecko"
    except Exception as exc:
        logger.debug("CoinGecko history %s %s: %s", symbol, on_date, exc)
        return None, ""


def _fetch_yahoo_history(symbol: str, on_date: date) -> tuple[Decimal | None, str]:
    from apps.pricing.providers.yahoo_equities import yahoo_ticker_for_symbol

    try:
        import yfinance as yf
    except ImportError:
        return None, ""

    ticker_symbol = yahoo_ticker_for_symbol(symbol)
    start = datetime(on_date.year, on_date.month, on_date.day, tzinfo=AMSTERDAM)
    end = start + timedelta(days=2)

    try:
        ticker = yf.Ticker(ticker_symbol)
        history = ticker.history(start=start.date(), end=end.date(), interval="1d")
        if history.empty:
            return None, ""
        row = history.iloc[0]
        price = row.get("Close")
        if price is None or price != price:
            return None, ""
        return Decimal(str(price)).quantize(Decimal("0.000001")), "yahoo"
    except Exception as exc:
        logger.debug("Yahoo history %s %s: %s", ticker_symbol, on_date, exc)
        return None, ""


def fetch_historical_prices(
    items: list[tuple[str, str, date]],
) -> dict[tuple[str, date], Decimal]:
    """Batch helper: (symbol, asset_type, date) -> price."""
    result: dict[tuple[str, date], Decimal] = {}
    for symbol, asset_type, on_date in items:
        price = fetch_historical_price_eur(symbol, asset_type, on_date)
        if price:
            result[(symbol.upper(), on_date)] = price
    return result
