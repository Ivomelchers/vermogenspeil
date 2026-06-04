"""Consistente bedragen uit transacties (o.a. DEGIRO zonder price_eur)."""

from decimal import Decimal

from apps.portfolio.models import TransactionType


def buy_cash_outflow_eur(
    *,
    quantity: Decimal,
    price_eur: Decimal | None,
    fee_eur: Decimal | None,
    total_eur: Decimal | None,
) -> Decimal:
    """
    Totale uitgave bij een koop (incl. kosten).
    DEGIRO-CSV: total_eur is het volledige afschrijfbedrag; fee zit daar vaak in.
    """
    if total_eur is not None and total_eur > 0:
        return total_eur
    price = price_eur or Decimal(0)
    return quantity * price + (fee_eur or Decimal(0))


def effective_unit_price_eur(
    *,
    quantity: Decimal,
    price_eur: Decimal | None,
    total_eur: Decimal | None,
) -> Decimal | None:
    """Stukprijs: uit CSV-koers of afgeleid uit total / aantal."""
    if price_eur is not None and price_eur > 0:
        return price_eur
    if quantity > 0 and total_eur is not None and total_eur > 0:
        return (total_eur / quantity).quantize(Decimal("0.000001"))
    return None


def transaction_buy_cash_outflow(tx) -> Decimal:
    if tx.transaction_type != TransactionType.BUY:
        return Decimal(0)
    return buy_cash_outflow_eur(
        quantity=tx.quantity,
        price_eur=tx.price_eur,
        fee_eur=tx.fee_eur,
        total_eur=tx.total_eur,
    )


def average_buy_unit_cost_eur(portfolio, asset_id: int) -> Decimal | None:
    """Gewogen gemiddelde kostprijs per stuk op basis van kooptransacties."""
    buys = portfolio.transactions.filter(
        asset_id=asset_id,
        transaction_type=TransactionType.BUY,
    )
    total_qty = Decimal(0)
    total_cost = Decimal(0)
    for tx in buys:
        line_cost = buy_cash_outflow_eur(
            quantity=tx.quantity,
            price_eur=tx.price_eur,
            fee_eur=tx.fee_eur,
            total_eur=tx.total_eur,
        )
        if line_cost <= 0:
            continue
        total_qty += tx.quantity
        total_cost += line_cost
    if total_qty <= 0:
        return None
    return (total_cost / total_qty).quantize(Decimal("0.000001"))
