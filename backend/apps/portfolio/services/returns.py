from decimal import Decimal

from apps.portfolio.models import TransactionType
from apps.portfolio.services.valuation import position_value_eur


def compute_return_summary(portfolio) -> dict:
    """
    Vereenvoudigd rendement op kostprijs (geen marktprijzen).
    Fase 3.3 basis — echte YTD met koersen volgt in 3.3/5.
    """
    invested = Decimal(0)
    for tx in portfolio.transactions.filter(transaction_type=TransactionType.BUY):
        price = tx.price_eur or Decimal(0)
        invested += tx.quantity * price + (tx.fee_eur or Decimal(0))

    current = Decimal(0)
    for position in portfolio.positions.select_related("asset"):
        current += position_value_eur(position)

    gain = current - invested
    pct = (gain / invested * Decimal(100)) if invested > 0 else Decimal(0)

    return {
        "invested_eur": invested.quantize(Decimal("0.01")),
        "current_value_eur": current.quantize(Decimal("0.01")),
        "unrealized_return_eur": gain.quantize(Decimal("0.01")),
        "unrealized_return_percent": pct.quantize(Decimal("0.01")),
        "method": "cost_basis",
        "note": "Verschil tussen huidige kostprijs-waarde en totale inleg. Geen live marktprijzen.",
    }
