import logging
from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from django.core.cache import cache
from django.utils import timezone

from apps.portfolio.models import AssetType
from apps.pricing.instrument_resolver import resolve_yahoo_ticker
from apps.pricing.providers.yahoo_equities import EQUITY_ASSET_TYPES
from apps.pricing.services.cache_keys import historical_price_cache_key
from apps.pricing.yfinance_utils import suppress_yfinance_noise

logger = logging.getLogger(__name__)

AMSTERDAM = ZoneInfo("Europe/Amsterdam")

COINGECKO_IDS = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
}

_CACHE_MISS = {"missing": True}


def _cache_is_miss(symbol: str, asset_type: str, on_date: date) -> bool:
    cached = cache.get(historical_price_cache_key(symbol, asset_type, on_date.isoformat()))
    return isinstance(cached, dict) and cached.get("missing") is True


def _cache_get(symbol: str, asset_type: str, on_date: date) -> Decimal | None:
    cached = cache.get(historical_price_cache_key(symbol, asset_type, on_date.isoformat()))
    if not cached or cached.get("missing"):
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


def _cache_set_miss(symbol: str, asset_type: str, on_date: date) -> None:
    from django.conf import settings

    ttl = min(getattr(settings, "PRICE_CACHE_TTL_HISTORICAL_SECONDS", 86400), 3600)
    cache.set(
        historical_price_cache_key(symbol, asset_type, on_date.isoformat()),
        _CACHE_MISS,
        timeout=ttl,
    )


def fetch_historical_price_eur(symbol: str, asset_type: str, on_date: date) -> Decimal | None:
    """Historische EUR-koers op een kalenderdag (Europe/Amsterdam)."""
    symbol = symbol.upper().strip()
    today = timezone.now().date()
    if on_date > today:
        return None

    cached = _cache_get(symbol, asset_type, on_date)
    if cached is not None:
        return cached
    if _cache_is_miss(symbol, asset_type, on_date):
        return None

    price: Decimal | None = None
    source = ""

    if asset_type == AssetType.CRYPTO:
        price, source = _fetch_coingecko_history(symbol, on_date)
    elif asset_type in EQUITY_ASSET_TYPES:
        price, source = _fetch_yahoo_history(symbol, on_date)

    if price and price > 0:
        _cache_set(symbol, asset_type, on_date, price, source)
        return price

    _cache_set_miss(symbol, asset_type, on_date)
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
    headers: dict[str, str] = {}
    from django.conf import settings

    key = getattr(settings, "COINGECKO_API_KEY", "") or ""
    if key:
        headers["x-cg-demo-api-key"] = key

    try:
        response = requests.get(
            url,
            params={"date": date_str, "localization": "false"},
            headers=headers,
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        price_eur = payload.get("market_data", {}).get("current_price", {}).get("eur")
        if price_eur is None:
            return None, ""
        return Decimal(str(price_eur)), "coingecko"
    except Exception as exc:
        logger.debug("CoinGecko history %s %s: %s", symbol, on_date, exc)
        return None, ""


def _close_from_history_frame(history, ticker_symbol: str) -> Decimal | None:
    if history is None or history.empty:
        return None
    try:
        if hasattr(history.columns, "levels") and ticker_symbol in history.columns.get_level_values(0):
            series = history[ticker_symbol]["Close"].dropna()
        elif "Close" in history.columns:
            series = history["Close"].dropna()
        else:
            return None
        if series.empty:
            return None
        price = series.iloc[-1]
        if price is None or price != price:
            return None
        return Decimal(str(price)).quantize(Decimal("0.000001"))
    except (KeyError, IndexError, InvalidOperation, TypeError):
        return None


def _fetch_yahoo_history(symbol: str, on_date: date) -> tuple[Decimal | None, str]:
    try:
        import yfinance as yf
    except ImportError:
        return None, ""

    ticker_symbol = resolve_yahoo_ticker(symbol)
    start = on_date - timedelta(days=7)
    end = on_date + timedelta(days=1)

    try:
        with suppress_yfinance_noise():
            history = yf.download(
                ticker_symbol,
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1d",
                progress=False,
                auto_adjust=True,
                threads=False,
            )
        price = _close_from_history_frame(history, ticker_symbol)
        if price and price > 0:
            return price, "yahoo"
        return None, ""
    except Exception as exc:
        logger.debug("Yahoo history %s %s: %s", ticker_symbol, on_date, exc)
        return None, ""


def _yahoo_batch_for_date(symbols: list[str], on_date: date) -> dict[str, Decimal]:
    """Eén yfinance-call voor meerdere symbolen op dezelfde datum."""
    if not symbols:
        return {}

    try:
        import yfinance as yf
    except ImportError:
        return {}

    ticker_map = {symbol.upper(): resolve_yahoo_ticker(symbol) for symbol in symbols}
    yahoo_symbols = list(dict.fromkeys(ticker_map.values()))
    start = on_date - timedelta(days=7)
    end = on_date + timedelta(days=1)

    try:
        with suppress_yfinance_noise():
            history = yf.download(
                " ".join(yahoo_symbols),
                start=start.isoformat(),
                end=end.isoformat(),
                interval="1d",
                progress=False,
                auto_adjust=True,
                group_by="ticker",
                threads=False,
            )
    except Exception as exc:
        logger.debug("Yahoo batch history %s: %s", on_date, exc)
        return {}

    result: dict[str, Decimal] = {}
    for portfolio_symbol, yahoo_symbol in ticker_map.items():
        price = _close_from_history_frame(history, yahoo_symbol)
        if price and price > 0:
            result[portfolio_symbol] = price
    return result


def _price_on_date_from_history(history, ticker_symbol: str, on_date: date) -> Decimal | None:
    """Extract the last close price on or before on_date from a multi-date history DataFrame."""
    if history is None or history.empty:
        return None
    try:
        import pandas as pd

        if hasattr(history.columns, "levels") and ticker_symbol in history.columns.get_level_values(0):
            series = history[ticker_symbol]["Close"].dropna()
        elif "Close" in history.columns:
            series = history["Close"].dropna()
        else:
            return None

        target = pd.Timestamp(on_date)
        available = series.index[series.index <= target]
        if available.empty:
            return None
        price_val = series[available[-1]]
        if price_val != price_val:  # NaN
            return None
        return Decimal(str(float(price_val))).quantize(Decimal("0.000001"))
    except Exception:
        return None


def prefetch_dates_into_cache(
    items: list[tuple[str, str]],
    dates: list[date],
) -> None:
    """
    Download the full date range for all equity symbols in ONE yfinance call and
    populate the price cache for every requested date.

    Replaces N sequential per-date fetches (each 2-3 s) with a single download,
    reducing 12-month value-history computation from ~30 s to ~3 s.
    """
    today = timezone.now().date()
    target_dates = sorted({d for d in dates if d < today})
    if not target_dates or not items:
        return

    equity_items = [
        (sym.upper().strip(), at)
        for sym, at in items
        if at in EQUITY_ASSET_TYPES
    ]
    if not equity_items:
        return

    # Skip dates that are already fully covered by the cache
    uncached_dates = [
        d for d in target_dates
        if any(
            _cache_get(sym, at, d) is None and not _cache_is_miss(sym, at, d)
            for sym, at in equity_items
        )
    ]
    if not uncached_dates:
        return

    try:
        import yfinance as yf
    except ImportError:
        return

    symbols = list({sym for sym, _ in equity_items})
    ticker_map = {sym: resolve_yahoo_ticker(sym) for sym in symbols}
    yahoo_symbols = list(dict.fromkeys(ticker_map.values()))

    fetch_start = (min(uncached_dates) - timedelta(days=7)).isoformat()
    fetch_end = (max(uncached_dates) + timedelta(days=1)).isoformat()

    try:
        with suppress_yfinance_noise():
            history = yf.download(
                yahoo_symbols if len(yahoo_symbols) > 1 else yahoo_symbols[0],
                start=fetch_start,
                end=fetch_end,
                interval="1d",
                progress=False,
                auto_adjust=True,
                group_by="ticker" if len(yahoo_symbols) > 1 else None,
                threads=False,
            )
    except Exception as exc:
        logger.debug("prefetch_dates_into_cache download failed: %s", exc)
        return

    if history is None or history.empty:
        return

    for sym, at in equity_items:
        yahoo_sym = ticker_map[sym]
        for on_date in uncached_dates:
            if _cache_get(sym, at, on_date) is not None or _cache_is_miss(sym, at, on_date):
                continue
            price = _price_on_date_from_history(history, yahoo_sym, on_date)
            if price and price > 0:
                _cache_set(sym, at, on_date, price, "yahoo")
            else:
                _cache_set_miss(sym, at, on_date)


def fetch_historical_prices(
    items: list[tuple[str, str, date]],
) -> dict[tuple[str, date], Decimal]:
    """Batch helper: (symbol, asset_type, date) -> price. Equity per datum gebundeld."""
    result: dict[tuple[str, date], Decimal] = {}
    today = timezone.now().date()

    equity_by_date: dict[date, list[str]] = defaultdict(list)
    equity_asset_type: dict[tuple[str, date], str] = {}
    other_items: list[tuple[str, str, date]] = []

    seen_equity: set[tuple[str, date]] = set()
    for symbol, asset_type, on_date in items:
        if on_date > today:
            continue
        symbol = symbol.upper().strip()
        key = (symbol, on_date)
        cached = _cache_get(symbol, asset_type, on_date)
        if cached is not None:
            result[key] = cached
            continue
        if _cache_is_miss(symbol, asset_type, on_date):
            continue

        if asset_type in EQUITY_ASSET_TYPES:
            if key not in seen_equity:
                seen_equity.add(key)
                equity_by_date[on_date].append(symbol)
                equity_asset_type[key] = asset_type
        else:
            other_items.append((symbol, asset_type, on_date))

    for on_date, symbols in equity_by_date.items():
        batch_prices = _yahoo_batch_for_date(symbols, on_date)
        for symbol in symbols:
            asset_type = equity_asset_type[(symbol, on_date)]
            price = batch_prices.get(symbol)
            if price and price > 0:
                _cache_set(symbol, asset_type, on_date, price, "yahoo")
                result[(symbol, on_date)] = price
            else:
                _cache_set_miss(symbol, asset_type, on_date)

    for symbol, asset_type, on_date in other_items:
        price = fetch_historical_price_eur(symbol, asset_type, on_date)
        if price:
            result[(symbol.upper(), on_date)] = price

    return result
