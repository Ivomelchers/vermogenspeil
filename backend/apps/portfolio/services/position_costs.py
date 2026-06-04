"""Hertel gemiddelde kostprijs op posities na import."""

from apps.portfolio.models import Portfolio
from apps.portfolio.services.transaction_amounts import average_buy_unit_cost_eur


def recompute_position_average_costs(portfolio: Portfolio) -> int:
    """Zet average_cost_eur op basis van kooptransacties. Returns aantal bijgewerkt."""
    updated = 0
    for position in portfolio.positions.select_related("asset"):
        avg = average_buy_unit_cost_eur(portfolio, position.asset_id)
        if avg is None:
            continue
        if position.average_cost_eur != avg:
            position.average_cost_eur = avg
            position.save(update_fields=["average_cost_eur", "updated_at"])
            updated += 1
    return updated
