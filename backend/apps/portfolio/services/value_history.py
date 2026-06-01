"""Vermogensverloop voor dashboard (kostprijs op peildata, huidige waarde op einde)."""

from datetime import date
from decimal import Decimal

from django.utils import timezone

from apps.portfolio.models import Portfolio
from apps.portfolio.services.historical_valuation import (
    _average_cost_eur,
    quantity_on_date,
)

MAX_POINTS = 14


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _unit_cost_eur(portfolio: Portfolio, position, on_date: date) -> Decimal | None:
    """Kostprijs uit transacties, anders uit positie (broker-sync)."""
    avg_cost = _average_cost_eur(portfolio, position.asset_id)
    if avg_cost and avg_cost > 0:
        return avg_cost
    if position.average_cost_eur and position.average_cost_eur > 0:
        return position.average_cost_eur
    return None


def _cost_basis_total_on_date(portfolio: Portfolio, on_date: date) -> Decimal:
    total = Decimal(0)
    for position in portfolio.positions.select_related("asset"):
        qty = quantity_on_date(portfolio, position.asset_id, on_date)
        if qty <= 0:
            continue
        unit_cost = _unit_cost_eur(portfolio, position, on_date)
        if unit_cost and unit_cost > 0:
            total += qty * unit_cost
    return total.quantize(Decimal("0.01"))


def _month_starts(from_date: date, to_date: date) -> list[date]:
    dates: list[date] = []
    year, month = from_date.year, from_date.month
    while True:
        point = date(year, month, 1)
        if point > to_date:
            break
        if point >= from_date:
            dates.append(point)
        month += 1
        if month > 12:
            month = 1
            year += 1
    return dates


def compute_value_history(
    portfolio: Portfolio,
    *,
    current_value_eur: Decimal,
    ytd_start_eur: Decimal | None = None,
    ytd_start_date: str | None = None,
) -> list[dict]:
    """
    Maandelijkse punten op kostprijs + actuele waarde vandaag.
    Geen externe koers-API per punt (snel genoeg voor dashboard).
    """
    today = timezone.now().date()
    first_tx = portfolio.transactions.order_by("occurred_at").values_list(
        "occurred_at", flat=True
    ).first()

    if not first_tx and current_value_eur <= 0:
        return []

    year_start = date(today.year, 1, 1)
    if first_tx:
        first_day = first_tx.date()
        range_start = min(year_start, date(first_day.year, first_day.month, 1))
    else:
        range_start = year_start

    sample_dates = _month_starts(range_start, today)
    if not sample_dates or sample_dates[-1] != today:
        sample_dates.append(today)

    if len(sample_dates) > MAX_POINTS:
        step = max(1, len(sample_dates) // (MAX_POINTS - 1))
        thinned = sample_dates[::step]
        if thinned[-1] != today:
            thinned.append(today)
        sample_dates = thinned[-MAX_POINTS:]

    points: list[dict] = []
    for on_date in sample_dates:
        if on_date == today:
            value = current_value_eur
            method = "current"
        else:
            value = _cost_basis_total_on_date(portfolio, on_date)
            method = "cost_basis"
        if value > 0 or on_date == today:
            points.append(
                {
                    "date": on_date.isoformat(),
                    "value_eur": _decimal_str(value),
                    "method": method,
                }
            )

    if not points and current_value_eur > 0:
        points.append(
            {
                "date": today.isoformat(),
                "value_eur": _decimal_str(current_value_eur),
                "method": "current",
            }
        )

    if len(points) < 2 and current_value_eur > 0:
        start_date = ytd_start_date or date(today.year, 1, 1).isoformat()
        start_value = ytd_start_eur if ytd_start_eur and ytd_start_eur > 0 else None
        if start_value is None:
            start_value = _cost_basis_total_on_date(
                portfolio, date.fromisoformat(start_date[:10])
            )
        if start_value is None or start_value <= 0:
            start_value = current_value_eur
        if not any(p["date"] == start_date for p in points):
            points.insert(
                0,
                {
                    "date": start_date[:10],
                    "value_eur": _decimal_str(start_value),
                    "method": "ytd_start",
                },
            )

    if len(points) == 1 and points[0]["date"] != today.isoformat():
        points.append(
            {
                "date": today.isoformat(),
                "value_eur": _decimal_str(current_value_eur),
                "method": "current",
            }
        )

    return points
