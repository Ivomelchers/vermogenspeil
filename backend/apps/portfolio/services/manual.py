import hashlib
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformType, SyncStatus
from apps.portfolio.models import (
    Asset,
    AssetType,
    Portfolio,
    Position,
    Transaction,
    TransactionType,
    VermogensCategorie,
)
from apps.portfolio.services import get_or_create_default_portfolio


def _manual_transaction_hash(
    *,
    user_id: int,
    asset_id: int,
    transaction_type: str,
    quantity: Decimal,
    price_eur: Decimal | None,
    occurred_at,
) -> str:
    raw = (
        f"manual|{user_id}|{asset_id}|{transaction_type}|{quantity}|"
        f"{price_eur}|{occurred_at.isoformat()}"
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def _rebuild_position(portfolio, asset: Asset) -> None:
    total = Decimal(0)
    for tx in portfolio.transactions.filter(asset=asset).order_by("occurred_at"):
        if tx.transaction_type == TransactionType.SELL:
            total -= tx.quantity
        elif tx.transaction_type == TransactionType.BUY:
            total += tx.quantity

    if total <= 0:
        Position.objects.filter(portfolio=portfolio, asset=asset).delete()
        return

    buys = portfolio.transactions.filter(
        asset=asset,
        transaction_type=TransactionType.BUY,
    )
    cost_qty = Decimal(0)
    cost_total = Decimal(0)
    for tx in buys:
        price = tx.price_eur or Decimal(0)
        cost_qty += tx.quantity
        cost_total += tx.quantity * price + (tx.fee_eur or Decimal(0))
    avg_cost = (cost_total / cost_qty) if cost_qty > 0 else None

    Position.objects.update_or_create(
        portfolio=portfolio,
        asset=asset,
        defaults={
            "quantity": total,
            "average_cost_eur": avg_cost,
        },
    )


def _ensure_manual_connection(user, portfolio) -> PlatformConnection:
    connection, _ = PlatformConnection.objects.get_or_create(
        user=user,
        platform=PlatformType.MANUAL,
        label="Handmatig",
        defaults={
            "portfolio": portfolio,
            "connection_method": ConnectionMethod.MANUAL,
            "is_active": True,
            "is_demo": False,
            "status": SyncStatus.SUCCESS,
            "last_synced_at": timezone.now(),
        },
    )
    return connection


@transaction.atomic
def create_manual_asset(
    user,
    *,
    symbol: str,
    name: str = "",
    asset_type: str = AssetType.OTHER,
    category: str = VermogensCategorie.BELEGGING,
) -> Asset:
    symbol = symbol.upper().strip()
    if not symbol:
        raise ValueError("Symbool is verplicht.")

    asset, created = Asset.objects.get_or_create(
        user=user,
        symbol=symbol,
        defaults={
            "name": name.strip() or symbol,
            "asset_type": asset_type,
            "category": category,
        },
    )
    if not created and name.strip():
        asset.name = name.strip()
        asset.asset_type = asset_type
        asset.category = category
        asset.save(update_fields=["name", "asset_type", "category", "updated_at"])

    portfolio = get_or_create_default_portfolio(user)
    _ensure_manual_connection(user, portfolio)
    return asset


@transaction.atomic
def create_manual_transaction(
    user,
    *,
    portfolio_id: int | None = None,
    asset_id: int,
    transaction_type: str,
    quantity: Decimal,
    price_eur: Decimal | None,
    fee_eur: Decimal = Decimal(0),
    occurred_at=None,
    notes: str = "",
) -> Transaction:
    if quantity <= 0:
        raise ValueError("Aantal moet groter dan 0 zijn.")

    if portfolio_id:
        portfolio = Portfolio.objects.for_user(user).filter(pk=portfolio_id).first()
        if not portfolio:
            raise ValueError("Portefeuille niet gevonden.")
    else:
        portfolio = get_or_create_default_portfolio(user)

    asset = Asset.objects.for_user(user).filter(pk=asset_id).first()
    if not asset:
        raise ValueError("Asset niet gevonden.")

    occurred = occurred_at or timezone.now()
    if transaction_type not in dict(TransactionType.choices):
        raise ValueError("Ongeldig transactietype.")

    total = None
    if price_eur is not None:
        total = quantity * price_eur + (fee_eur or Decimal(0))

    tx_hash = _manual_transaction_hash(
        user_id=user.pk,
        asset_id=asset.pk,
        transaction_type=transaction_type,
        quantity=quantity,
        price_eur=price_eur,
        occurred_at=occurred,
    )

    transaction_obj, created = Transaction.objects.get_or_create(
        portfolio=portfolio,
        transaction_hash=tx_hash,
        defaults={
            "asset": asset,
            "transaction_type": transaction_type,
            "quantity": quantity,
            "price_eur": price_eur,
            "fee_eur": fee_eur or Decimal(0),
            "total_eur": total,
            "occurred_at": occurred,
            "external_id": f"manual-{tx_hash[:12]}",
            "source_platform": PlatformType.MANUAL,
            "notes": notes,
        },
    )
    if not created:
        raise ValueError("Deze transactie bestaat al.")

    if transaction_type in (TransactionType.BUY, TransactionType.SELL):
        _rebuild_position(portfolio, asset)

    _ensure_manual_connection(user, portfolio)
    return transaction_obj
