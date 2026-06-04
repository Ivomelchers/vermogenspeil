from decimal import Decimal

from apps.portfolio.models import TransactionType
from apps.pricing.services import PriceQuote
from apps.portfolio.services.transaction_amounts import transaction_buy_cash_outflow
from apps.portfolio.services.valuation import position_value_eur


def compute_return_summary(portfolio, live_prices: dict[str, PriceQuote] | None = None) -> dict:
    """Rendement: inleg vs huidige waarde (marktwaarde waar beschikbaar)."""
    invested = Decimal(0)
    for tx in portfolio.transactions.filter(transaction_type=TransactionType.BUY):
        invested += transaction_buy_cash_outflow(tx)

    current = Decimal(0)
    market_positions = 0
    total_positions = 0
    for position in portfolio.positions.select_related("asset"):
        if position.quantity <= 0:
            continue
        total_positions += 1
        value, source = position_value_eur(position, live_prices=live_prices)
        current += value
        if source == "market":
            market_positions += 1

    gain = current - invested
    pct = (gain / invested * Decimal(100)) if invested > 0 else Decimal(0)

    if market_positions == total_positions and total_positions > 0:
        method = "market"
        note = "Verschil tussen marktwaarde en totale inleg."
    elif market_positions > 0:
        method = "mixed"
        note = "Deels marktwaarde, deels kostprijs voor posities zonder koers."
    else:
        method = "cost_basis"
        note = "Verschil tussen kostprijs-waarde en totale inleg. Geen live marktprijzen."

    return {
        "invested_eur": invested.quantize(Decimal("0.01")),
        "current_value_eur": current.quantize(Decimal("0.01")),
        "unrealized_return_eur": gain.quantize(Decimal("0.01")),
        "unrealized_return_percent": pct.quantize(Decimal("0.01")),
        "method": method,
        "note": note,
    }
