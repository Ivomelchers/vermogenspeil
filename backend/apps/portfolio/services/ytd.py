import logging
from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.portfolio.models import Portfolio
from apps.portfolio.services.historical_valuation import portfolio_valuation_at_date
from apps.portfolio.services.valuation import fetch_live_prices_for_positions, position_value_eur
from apps.snapshots.models import PeilDatumSnapshot

logger = logging.getLogger(__name__)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


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
    market_positions = 0
    valued_positions = 0
    for position in positions:
        if position.quantity <= 0:
            continue
        value, source = position_value_eur(position, live_prices=live_prices)
        if value <= 0:
            continue
        valued_positions += 1
        current += value
        if source == "market":
            market_positions += 1

    if valued_positions == 0:
        current_method = "cost_basis"
    elif market_positions == valued_positions:
        current_method = "market"
    elif market_positions > 0:
        current_method = "mixed"
    else:
        current_method = "cost_basis"

    snapshot = PeilDatumSnapshot.objects.filter(user=user, year=year).first()
    if snapshot and snapshot.data.get("has_portfolio"):
        start = Decimal(str(snapshot.data.get("total_value_eur", "0")))
        start_method = "peildatum_snapshot"
        start_label = snapshot.data.get("peildatum", jan_first.isoformat())
    else:
        hist = portfolio_valuation_at_date(portfolio, jan_first)
        start = hist["total_value_eur"]
        start_method = hist["valuation_method"]
        start_label = jan_first.isoformat()

    if start <= 0 and current <= 0:
        return {
            "year": year,
            "available": False,
            "note": "Geen posities om YTD-rendement te berekenen.",
        }

    gain = current - start
    pct = (gain / start * Decimal(100)) if start > 0 else Decimal(0)
    trusted = True
    if current_method == "cost_basis" and current > 0:
        trusted = False
    if current_method == "mixed" and market_positions == 0:
        trusted = False
    if start_method == "peildatum_snapshot" and current_method == "cost_basis":
        trusted = False

    return {
        "year": year,
        "available": True,
        "trusted": trusted,
        "start_value_eur": _decimal_str(start),
        "current_value_eur": _decimal_str(current),
        "ytd_return_eur": _decimal_str(gain),
        "ytd_return_percent": _decimal_str(pct),
        "start_method": start_method,
        "start_as_of": start_label,
        "current_method": current_method,
        "note": (
            "YTD: verschil tussen huidige waarde en startwaarde dit jaar "
            "(peildatum-snapshot of koersen op 1 januari)."
        ),
    }
