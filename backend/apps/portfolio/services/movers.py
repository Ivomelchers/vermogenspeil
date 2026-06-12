"""Top winnaars en verliezers per periode (FSD §5.1)."""

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.portfolio.models import Portfolio
from apps.portfolio.services.historical_valuation import (
    _average_cost_eur,
    quantity_on_date,
)
from apps.portfolio.services.valuation import fetch_live_prices_for_positions, position_value_eur
from apps.pricing.services.historical import fetch_historical_prices

PERIODS = ("day", "week", "month", "ytd")


def period_start(period: str, *, today: date | None = None) -> date:
    today = today or timezone.now().date()
    if period == "day":
        return today - timedelta(days=1)
    if period == "week":
        return today - timedelta(days=7)
    if period == "month":
        return today - timedelta(days=30)
    if period == "ytd":
        return date(today.year, 1, 1)
    return today - timedelta(days=30)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _position_value_at_date(
    portfolio: Portfolio,
    position,
    on_date: date,
    *,
    price_cache: dict[tuple[str, date], Decimal],
    tx_cache: list | None = None,
) -> tuple[Decimal, str]:
    qty = quantity_on_date(portfolio, position.asset_id, on_date, tx_cache=tx_cache)
    if qty <= 0:
        return Decimal(0), "zero"

    symbol = position.asset.symbol.upper()
    price = price_cache.get((symbol, on_date))
    if price and price > 0:
        return (qty * price).quantize(Decimal("0.01")), "historical"

    avg_cost = _average_cost_eur(portfolio, position.asset_id)
    if avg_cost and avg_cost > 0:
        return (qty * avg_cost).quantize(Decimal("0.01")), "cost_basis_fallback"

    if position.average_cost_eur and position.average_cost_eur > 0:
        return (qty * position.average_cost_eur).quantize(Decimal("0.01")), "cost_basis"

    return Decimal(0), "unpriced"


def compute_top_movers(
    portfolio: Portfolio,
    period: str = "month",
    *,
    limit: int = 3,
    price_cache: dict[tuple[str, date], Decimal] | None = None,
    tx_cache: list | None = None,
    live_prices: dict | None = None,
    positions: list | None = None,
) -> dict:
    if period not in PERIODS:
        period = "month"

    start = period_start(period)
    if positions is None:
        positions = list(portfolio.positions.select_related("asset"))
    if live_prices is None:
        live_prices = fetch_live_prices_for_positions(positions)

    if price_cache is None:
        items = []
        for position in positions:
            if quantity_on_date(portfolio, position.asset_id, start, tx_cache=tx_cache) > 0:
                items.append((position.asset.symbol, position.asset.asset_type, start))
        price_cache = fetch_historical_prices(items)

    movers: list[dict] = []
    for position in positions:
        current_value, _ = position_value_eur(position, live_prices=live_prices)
        if current_value <= 0:
            continue

        if quantity_on_date(portfolio, position.asset_id, start, tx_cache=tx_cache) <= 0:
            continue

        start_value, start_source = _position_value_at_date(
            portfolio, position, start, price_cache=price_cache, tx_cache=tx_cache
        )
        if start_value <= 0:
            continue

        change_eur = current_value - start_value
        change_percent = (change_eur / start_value) * Decimal(100)

        movers.append(
            {
                "position_id": position.id,
                "symbol": position.asset.symbol,
                "name": position.asset.name or position.asset.symbol,
                "start_value_eur": _decimal_str(start_value),
                "current_value_eur": _decimal_str(current_value),
                "change_eur": _decimal_str(change_eur),
                "change_percent": _decimal_str(change_percent),
                "valuation_start": start_source,
            }
        )

    gainers = sorted(
        (m for m in movers if Decimal(m["change_eur"]) > 0),
        key=lambda m: Decimal(m["change_eur"]),
        reverse=True,
    )[:limit]
    losers = sorted(
        (m for m in movers if Decimal(m["change_eur"]) < 0),
        key=lambda m: Decimal(m["change_eur"]),
    )[:limit]

    return {
        "period": period,
        "period_start": start.isoformat(),
        "gainers": gainers,
        "losers": losers,
    }


def compute_all_top_movers(portfolio: Portfolio, *, limit: int = 3) -> dict:
    """Alle periodes met één gebundelde historische koers-fetch en één transactie-fetch."""
    positions = list(portfolio.positions.select_related("asset"))
    live_prices = fetch_live_prices_for_positions(positions)

    # Pre-load all buy/sell transactions once — avoids N×4 queries in quantity_on_date
    tx_cache = list(
        portfolio.transactions.filter(transaction_type__in=["buy", "sell"])
    )

    starts = {p: period_start(p) for p in PERIODS}
    items: list[tuple[str, str, date]] = []
    seen: set[tuple[str, str, date]] = set()
    for start in starts.values():
        for position in positions:
            if quantity_on_date(portfolio, position.asset_id, start, tx_cache=tx_cache) <= 0:
                continue
            key = (position.asset.symbol.upper(), position.asset.asset_type, start)
            if key not in seen:
                seen.add(key)
                items.append(key)

    # Batch-prefetch ALL period dates in ONE yfinance download before per-date fetches
    if items and positions:
        from apps.pricing.services.historical import prefetch_dates_into_cache
        equity_items = [(pos.asset.symbol, pos.asset.asset_type) for pos in positions]
        unique_dates = list({d for _, _, d in items})
        prefetch_dates_into_cache(equity_items, unique_dates)

    price_cache = fetch_historical_prices(items) if items else {}

    return {
        period: compute_top_movers(
            portfolio, period, limit=limit,
            price_cache=price_cache, tx_cache=tx_cache,
            live_prices=live_prices, positions=positions,
        )
        for period in PERIODS
    }
