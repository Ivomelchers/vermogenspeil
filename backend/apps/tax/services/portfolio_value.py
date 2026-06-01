from decimal import Decimal

from apps.portfolio.models import Portfolio
from apps.portfolio.services.valuation import fetch_live_prices_for_positions, position_value_eur


def current_portfolio_value_eur(portfolio: Portfolio) -> Decimal:
    positions = list(portfolio.positions.select_related("asset"))
    live_prices = fetch_live_prices_for_positions(positions)
    total = Decimal(0)
    for position in positions:
        value, _ = position_value_eur(position, live_prices=live_prices)
        if value > 0:
            total += value
    return total.quantize(Decimal("0.01"))
