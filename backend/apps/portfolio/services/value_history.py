"""Vermogensverloop voor dashboard: portfolio-waarde vs cost basis (FSD §5.1 / §6.1)."""

from datetime import date, timedelta
from decimal import Decimal

from django.utils import timezone

from apps.portfolio.models import Portfolio
from apps.portfolio.services.historical_valuation import (
    _average_cost_eur,
    portfolio_valuation_at_date,
    quantity_on_date,
)

MAX_POINTS = 14
AMSTERDAM_MONTHS = 12


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _unit_cost_eur(portfolio: Portfolio, position, on_date: date) -> Decimal | None:
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


def _portfolio_value_on_date(portfolio: Portfolio, on_date: date) -> Decimal:
    if on_date >= timezone.now().date():
        return Decimal(0)
    result = portfolio_valuation_at_date(portfolio, on_date)
    return result["total_value_eur"]


def _month_starts_last_12(to_date: date) -> list[date]:
    """Maandstarts over maximaal 12 maanden, eindigend op de maand van to_date."""
    dates: list[date] = []
    year, month = to_date.year, to_date.month
    for _ in range(AMSTERDAM_MONTHS):
        point = date(year, month, 1)
        dates.append(point)
        month -= 1
        if month < 1:
            month = 12
            year -= 1
    dates.reverse()
    return dates


def compute_value_history(
    portfolio: Portfolio,
    *,
    current_value_eur: Decimal,
    ytd_start_eur: Decimal | None = None,
    ytd_start_date: str | None = None,
) -> list[dict]:
    """
    Maandelijkse punten: portfolio-waarde (historisch) + cost basis.
    Laatste punt: actuele marktwaarde + huidige cost basis.
    """
    today = timezone.now().date()
    range_start = today - timedelta(days=365)
    sample_dates = [d for d in _month_starts_last_12(today) if d >= range_start]
    if not sample_dates or sample_dates[-1].month != today.month:
        sample_dates.append(date(today.year, today.month, 1))
    if sample_dates[-1] != today:
        sample_dates.append(today)

    if len(sample_dates) > MAX_POINTS:
        step = max(1, len(sample_dates) // (MAX_POINTS - 1))
        thinned = sample_dates[::step]
        if thinned[-1] != today:
            thinned.append(today)
        sample_dates = thinned[-MAX_POINTS:]

    current_cost = _cost_basis_total_on_date(portfolio, today)
    points: list[dict] = []

    for on_date in sample_dates:
        if on_date == today:
            portfolio_value = current_value_eur
            cost_basis = current_cost
            method = "current"
        else:
            portfolio_value = _portfolio_value_on_date(portfolio, on_date)
            if portfolio_value <= 0:
                portfolio_value = _cost_basis_total_on_date(portfolio, on_date)
            cost_basis = _cost_basis_total_on_date(portfolio, on_date)
            method = "historical" if portfolio_value > 0 else "cost_basis"

        if portfolio_value > 0 or cost_basis > 0 or on_date == today:
            points.append(
                {
                    "date": on_date.isoformat(),
                    "value_eur": _decimal_str(portfolio_value),
                    "cost_basis_eur": _decimal_str(cost_basis),
                    "method": method,
                }
            )

    if not points and current_value_eur > 0:
        points.append(
            {
                "date": today.isoformat(),
                "value_eur": _decimal_str(current_value_eur),
                "cost_basis_eur": _decimal_str(current_cost),
                "method": "current",
            }
        )

    if len(points) < 2 and current_value_eur > 0:
        start_date = ytd_start_date or date(today.year, 1, 1).isoformat()
        start_value = ytd_start_eur if ytd_start_eur and ytd_start_eur > 0 else None
        start_cost = _cost_basis_total_on_date(portfolio, date.fromisoformat(start_date[:10]))
        if start_value is None or start_value <= 0:
            start_value = start_cost if start_cost > 0 else current_value_eur
        if not any(p["date"] == start_date[:10] for p in points):
            points.insert(
                0,
                {
                    "date": start_date[:10],
                    "value_eur": _decimal_str(start_value),
                    "cost_basis_eur": _decimal_str(start_cost),
                    "method": "ytd_start",
                },
            )

    return points


def compute_hero_delta_30d(
    portfolio: Portfolio,
    *,
    current_value_eur: Decimal,
) -> dict:
    """Delta totaalvermogen over ~30 dagen (FSD §5.1 hero-kaart)."""
    today = timezone.now().date()
    start_date = today - timedelta(days=30)
    start_value = _portfolio_value_on_date(portfolio, start_date)
    if start_value <= 0:
        start_value = _cost_basis_total_on_date(portfolio, start_date)

    if start_value <= 0:
        return {
            "available": False,
            "start_date": start_date.isoformat(),
            "note": "Onvoldoende historie voor 30-dagen delta.",
        }

    change_eur = current_value_eur - start_value
    change_percent = (change_eur / start_value) * Decimal(100)
    return {
        "available": True,
        "start_date": start_date.isoformat(),
        "start_value_eur": _decimal_str(start_value),
        "change_eur": _decimal_str(change_eur),
        "change_percent": _decimal_str(change_percent),
    }
