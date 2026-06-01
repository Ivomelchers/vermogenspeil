import hashlib
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.integrations.base import BalanceHolding, PlatformAdapterError, TradeRecord
from apps.integrations.models import PlatformType, SyncStatus
from apps.portfolio.models import (
    Asset,
    AssetType,
    Position,
    Transaction,
    TransactionType,
    VermogensCategorie,
)

logger = logging.getLogger(__name__)


def _transaction_hash(
    *,
    platform: str,
    external_id: str,
    symbol: str,
    side: str,
    quantity: Decimal,
    price: Decimal,
    occurred_at,
) -> str:
    raw = f"{platform}|{external_id}|{symbol}|{side}|{quantity}|{price}|{occurred_at.isoformat()}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_or_create_asset(
    user,
    symbol: str,
    *,
    asset_type: str = AssetType.CRYPTO,
    name: str = "",
) -> Asset:
    asset, _ = Asset.objects.get_or_create(
        user=user,
        symbol=symbol,
        defaults={
            "name": name or symbol,
            "asset_type": asset_type,
            "category": VermogensCategorie.BELEGGING,
        },
    )
    return asset


def _map_trade_type(side: str) -> str:
    if side.lower() == "sell":
        return TransactionType.SELL
    return TransactionType.BUY


@transaction.atomic
def apply_sync_results(connection, balances: list[BalanceHolding], trades: list[TradeRecord]) -> tuple[int, int]:
    user = connection.user
    portfolio = connection.portfolio
    positions_updated = 0
    transactions_synced = 0

    for holding in balances:
        asset = _get_or_create_asset(
            user,
            holding.symbol,
            asset_type=holding.asset_type or AssetType.CRYPTO,
            name=holding.name,
        )
        position, created = Position.objects.update_or_create(
            portfolio=portfolio,
            asset=asset,
            defaults={"quantity": holding.quantity},
        )
        if created or position.quantity != holding.quantity:
            positions_updated += 1

    for trade in trades:
        asset = _get_or_create_asset(
            user,
            trade.symbol,
            asset_type=trade.asset_type or AssetType.CRYPTO,
        )
        tx_hash = _transaction_hash(
            platform=connection.platform,
            external_id=trade.external_id or "",
            symbol=trade.symbol,
            side=trade.side,
            quantity=trade.quantity,
            price=trade.price_eur,
            occurred_at=trade.occurred_at,
        )
        total = trade.quantity * trade.price_eur
        _, created = Transaction.objects.get_or_create(
            portfolio=portfolio,
            transaction_hash=tx_hash,
            defaults={
                "asset": asset,
                "transaction_type": _map_trade_type(trade.side),
                "quantity": trade.quantity,
                "price_eur": trade.price_eur,
                "fee_eur": trade.fee_eur,
                "total_eur": total,
                "occurred_at": trade.occurred_at,
                "external_id": trade.external_id,
                "source_platform": connection.platform,
            },
        )
        if created:
            transactions_synced += 1

    connection.status = SyncStatus.SUCCESS
    connection.last_synced_at = timezone.now()
    connection.last_error = ""
    connection.save(update_fields=["status", "last_synced_at", "last_error", "updated_at"])

    return positions_updated, transactions_synced


def get_adapter(connection):
    if connection.is_demo:
        from apps.integrations.demo.adapter import DemoPlatformAdapter

        return DemoPlatformAdapter(connection)

    from apps.integrations.bitvavo.adapter import BitvavoPlatformAdapter

    adapters = {
        PlatformType.BITVAVO: BitvavoPlatformAdapter,
    }
    adapter_cls = adapters.get(connection.platform)
    if not adapter_cls:
        raise PlatformAdapterError(f"Platform {connection.platform} wordt nog niet ondersteund.")
    return adapter_cls(connection)


def run_connection_sync(sync_job_id: int) -> None:
    from apps.integrations.models import SyncJob

    sync_job = SyncJob.objects.select_related("connection", "connection__user", "connection__portfolio").get(
        pk=sync_job_id
    )
    connection = sync_job.connection

    sync_job.status = SyncStatus.RUNNING
    sync_job.started_at = timezone.now()
    sync_job.save(update_fields=["status", "started_at"])

    connection.status = SyncStatus.RUNNING
    connection.save(update_fields=["status", "updated_at"])

    try:
        adapter = get_adapter(connection)
        positions, transactions = adapter.sync()
        sync_job.positions_synced = positions
        sync_job.transactions_synced = transactions
        sync_job.status = SyncStatus.SUCCESS
        sync_job.error_message = ""
    except (PlatformAdapterError, Exception) as exc:
        logger.exception("Sync failed for connection %s", connection.id)
        message = str(exc)
        sync_job.status = SyncStatus.ERROR
        sync_job.error_message = message
        connection.status = SyncStatus.ERROR
        connection.last_error = message
        connection.save(update_fields=["status", "last_error", "updated_at"])
    finally:
        sync_job.completed_at = timezone.now()
        sync_job.save(
            update_fields=[
                "status",
                "positions_synced",
                "transactions_synced",
                "error_message",
                "completed_at",
            ]
        )
