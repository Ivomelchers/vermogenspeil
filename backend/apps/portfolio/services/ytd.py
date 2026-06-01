import logging
from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.portfolio.models import Portfolio, TransactionType
from apps.portfolio.services.valuation import fetch_live_prices_for_positions, position_value_eur
from apps.pricing.services.historical import fetch_historical_price_eur
from apps.snapshots.models import PeilDatumSnapshot

logger = logging.getLogger(__name__)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _quantity_on_date(portfolio, asset_id: int, on_date: date) -> Decimal:
    """Netto aantal asset op einde van on_date (vereenvoudigd: alle tx t/m die dag)."""
    from datetime import datetime
    from zoneinfo import ZoneInfo

    cutoff = datetime(
        on_date.year,
        on_date.month,
        on_date.day,
        23,
        59,
        59,
        tzinfo=ZoneInfo("Europe/Amsterdam"),
    )
    total = Decimal(0)
    for tx in portfolio.transactions.filter(asset_id=asset_id, occurred_at__lte=cutoff):
        if tx.transaction_type == TransactionType.SELL:
            total -= tx.quantity
        elif tx.transaction_type == TransactionType.BUY:
            total += tx.quantity
    return total


def _portfolio_value_on_date(portfolio, on_date: date) -> tuple[Decimal, str]:
    """Waarde portefeuille op datum via historische koersen."""
    total = Decimal(0)
    priced = 0
    total_positions = 0

    assets_seen: set[int] = set()
    for tx in portfolio.transactions.select_related("asset").order_by("occurred_at"):
        assets_seen.add(tx.asset_id)

    for asset_id in assets_seen:
        sample_tx = portfolio.transactions.filter(asset_id=asset_id).first()
        if not sample_tx:
            continue
        asset = sample_tx.asset
        qty = _quantity_on_date(portfolio, asset_id, on_date)
        if qty <= 0:
            continue
        total_positions += 1

        price = fetch_historical_price_eur(asset.symbol, asset.asset_type, on_date)
        if price:
            total += qty * price
            priced += 1
        elif sample_tx.price_eur:
            total += qty * sample_tx.price_eur
            priced += 1

    if total_positions == 0:
        return Decimal(0), "empty"

    method = "historical_prices" if priced == total_positions else "mixed_historical"
    return total.quantize(Decimal("0.01")), method


def compute_ytd_summary(portfolio: Portfolio, user, *, year: int | None = None) -> dict:
    """
    YTD-rendement: huidige marktwaarde vs startwaarde (peildatum-snapshot of 1 jan historisch).
    Indirect rendement via koersbeweging dit kalenderjaar.
    """
    year = year or timezone.now().year
    jan_first = date(year, 1, 1)

    positions = list(portfolio.positions.select_related("asset"))
    live_prices = fetch_live_prices_for_positions(positions)

    current = Decimal(0)
    for position in positions:
        value, _ = position_value_eur(position, live_prices=live_prices)
        current += value

    snapshot = PeilDatumSnapshot.objects.filter(user=user, year=year).first()
    if snapshot and snapshot.data.get("has_portfolio"):
        start = Decimal(str(snapshot.data.get("total_value_eur", "0")))
        start_method = "peildatum_snapshot"
        start_label = snapshot.data.get("peildatum", jan_first.isoformat())
    else:
        start, start_method = _portfolio_value_on_date(portfolio, jan_first)
        start_label = jan_first.isoformat()

    if start <= 0 and current <= 0:
        return {
            "year": year,
            "available": False,
            "note": "Geen posities om YTD-rendement te berekenen.",
        }

    gain = current - start
    pct = (gain / start * Decimal(100)) if start > 0 else Decimal(0)

    return {
        "year": year,
        "available": True,
        "start_value_eur": _decimal_str(start),
        "current_value_eur": _decimal_str(current),
        "ytd_return_eur": _decimal_str(gain),
        "ytd_return_percent": _decimal_str(pct),
        "start_method": start_method,
        "start_as_of": start_label,
        "current_method": "market" if live_prices else "cost_basis",
        "note": (
            "YTD: verschil tussen huidige waarde en startwaarde dit jaar "
            "(peildatum-snapshot of koersen op 1 januari)."
        ),
    }
