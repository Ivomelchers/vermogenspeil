"""Historische portefeuillewaarde op een peildatum (1 januari)."""

from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from apps.portfolio.models import Portfolio, TransactionType
from apps.pricing.services.historical import fetch_historical_price_eur, fetch_historical_prices

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def quantity_on_date(
    portfolio: Portfolio,
    asset_id: int,
    on_date: date,
    *,
    tx_cache: list | None = None,
) -> Decimal:
    """Netto positie op einde van on_date (alle transacties t/m die dag)."""
    cutoff = datetime(on_date.year, on_date.month, on_date.day, 23, 59, 59, tzinfo=AMSTERDAM)

    if tx_cache is not None:
        txs = [tx for tx in tx_cache if tx.asset_id == asset_id and tx.occurred_at <= cutoff]
    else:
        txs = list(portfolio.transactions.filter(asset_id=asset_id, occurred_at__lte=cutoff))

    total = Decimal(0)
    for tx in txs:
        if tx.transaction_type == TransactionType.SELL:
            total -= tx.quantity
        elif tx.transaction_type == TransactionType.BUY:
            total += tx.quantity
    return total


def _average_cost_eur(portfolio: Portfolio, asset_id: int) -> Decimal | None:
    from apps.portfolio.services.transaction_amounts import average_buy_unit_cost_eur

    return average_buy_unit_cost_eur(portfolio, asset_id)


def position_value_on_peildatum(
    portfolio: Portfolio,
    position,
    on_date: date,
    *,
    price_cache: dict[tuple[str, date], Decimal] | None = None,
    tx_cache: list | None = None,
) -> tuple[Decimal, str]:
    """
    Waarde van één positie op peildatum.
    Returns (value_eur, valuation_source).
    """
    qty = quantity_on_date(portfolio, position.asset_id, on_date, tx_cache=tx_cache)
    if qty <= 0:
        return Decimal(0), "zero_on_peildatum"

    symbol = position.asset.symbol.upper()
    asset_type = position.asset.asset_type

    price: Decimal | None = None
    if price_cache is not None:
        price = price_cache.get((symbol, on_date))
    if price is None:
        price = fetch_historical_price_eur(symbol, asset_type, on_date)

    if price and price > 0:
        return (qty * price).quantize(Decimal("0.01")), "historical"

    avg_cost = _average_cost_eur(portfolio, position.asset_id)
    if avg_cost:
        return (qty * avg_cost).quantize(Decimal("0.01")), "cost_basis_fallback"

    return Decimal(0), "unpriced"


def portfolio_valuation_at_date(
    portfolio: Portfolio,
    on_date: date,
    *,
    tx_cache: list | None = None,
) -> dict:
    """
    Waardeer alle posities op peildatum met historische koersen waar beschikbaar.
    """
    positions = list(portfolio.positions.select_related("asset"))
    if not positions:
        return {
            "total_value_eur": Decimal(0),
            "valuation_method": "empty",
            "positions": [],
            "historical_priced": 0,
            "total_positions": 0,
        }

    fetch_items = [
        (pos.asset.symbol, pos.asset.asset_type, on_date)
        for pos in positions
        if quantity_on_date(portfolio, pos.asset_id, on_date, tx_cache=tx_cache) > 0
    ]
    price_cache = fetch_historical_prices(fetch_items)

    rows = []
    total = Decimal(0)
    historical_count = 0
    valued_count = 0

    for position in positions:
        value, source = position_value_on_peildatum(
            portfolio,
            position,
            on_date,
            price_cache=price_cache,
            tx_cache=tx_cache,
        )
        if value <= 0:
            continue
        valued_count += 1
        total += value
        if source == "historical":
            historical_count += 1

        unit_price = price_cache.get((position.asset.symbol.upper(), on_date))
        row = {
            "position": position,
            "quantity": quantity_on_date(portfolio, position.asset_id, on_date, tx_cache=tx_cache),
            "value_eur": value,
            "valuation_source": source,
            "unit_price_eur": unit_price,
        }
        rows.append(row)

    if valued_count == 0:
        method = "empty"
    elif historical_count == valued_count:
        method = "historical_prices"
    elif historical_count > 0:
        method = "mixed_historical"
    else:
        method = "cost_basis_fallback"

    return {
        "total_value_eur": total.quantize(Decimal("0.01")),
        "valuation_method": method,
        "positions": rows,
        "historical_priced": historical_count,
        "total_positions": valued_count,
    }
