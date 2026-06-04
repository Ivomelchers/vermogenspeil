from decimal import Decimal

from apps.portfolio.models import TransactionType
from apps.pricing.services import PriceQuote
from apps.portfolio.services.transaction_amounts import transaction_buy_cash_outflow
from apps.portfolio.services.valuation import position_cost_value_eur, position_value_eur


def compute_return_summary(portfolio, live_prices: dict[str, PriceQuote] | None = None) -> dict:
    """Rendement: kostprijs open posities vs huidige waarde (markt waar beschikbaar)."""
    total_buy_outflow = Decimal(0)
    for tx in portfolio.transactions.filter(transaction_type=TransactionType.BUY):
        total_buy_outflow += transaction_buy_cash_outflow(tx)

    current = Decimal(0)
    cost_basis = Decimal(0)
    market_positions = 0
    total_positions = 0
    for position in portfolio.positions.select_related("asset"):
        if position.quantity <= 0:
            continue
        total_positions += 1
        value, source = position_value_eur(position, live_prices=live_prices)
        current += value
        cost_basis += position_cost_value_eur(position)
        if source == "market":
            market_positions += 1

    gain = current - cost_basis
    pct = (gain / cost_basis * Decimal(100)) if cost_basis > 0 else Decimal(0)

    if market_positions == total_positions and total_positions > 0:
        method = "market"
    elif market_positions > 0:
        method = "mixed"
    else:
        method = "cost_basis"

    return {
        "invested_eur": cost_basis.quantize(Decimal("0.01")),
        "cost_basis_eur": cost_basis.quantize(Decimal("0.01")),
        "total_buy_outflow_eur": total_buy_outflow.quantize(Decimal("0.01")),
        "current_value_eur": current.quantize(Decimal("0.01")),
        "unrealized_return_eur": gain.quantize(Decimal("0.01")),
        "unrealized_return_percent": pct.quantize(Decimal("0.01")),
        "method": method,
    }
