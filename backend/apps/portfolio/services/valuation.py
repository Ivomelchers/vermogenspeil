from decimal import Decimal

from apps.portfolio.models import AssetType, Position, TransactionType


def _cost_basis_from_transactions(position: Position) -> Decimal | None:
    buys = position.portfolio.transactions.filter(
        asset=position.asset,
        transaction_type=TransactionType.BUY,
    )
    total_qty = Decimal(0)
    total_cost = Decimal(0)
    for tx in buys:
        price = tx.price_eur or Decimal(0)
        total_qty += tx.quantity
        total_cost += tx.quantity * price + (tx.fee_eur or Decimal(0))

    if total_qty <= 0:
        return None

    return total_cost / total_qty


def position_value_eur(position: Position) -> Decimal:
    """Waarde op basis van kostprijs — marktprijzen volgen in fase 5."""
    if position.quantity <= 0:
        return Decimal(0)

    unit_cost = position.average_cost_eur
    if unit_cost is None:
        unit_cost = _cost_basis_from_transactions(position)

    if unit_cost is None:
        return Decimal(0)

    return position.quantity * unit_cost


def asset_type_label(asset_type: str) -> str:
    mapping = {
        AssetType.CRYPTO: "Crypto",
        AssetType.STOCK: "Beleggingen",
        AssetType.ETF: "Beleggingen",
        AssetType.FUND: "Beleggingen",
        AssetType.METAL: "Edelmetalen",
        AssetType.CASH: "Sparen",
        AssetType.OTHER: "Overig",
    }
    return mapping.get(asset_type, "Overig")
