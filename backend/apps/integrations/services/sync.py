import hashlib
import logging
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.integrations.base import BalanceHolding, PlatformAdapterError, TradeRecord
from apps.integrations.models import ConnectionMethod, PlatformType, SyncStatus
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
    category = (
        VermogensCategorie.BANKTEGOED
        if asset_type == AssetType.CASH
        else VermogensCategorie.BELEGGING
    )
    asset, _ = Asset.objects.get_or_create(
        user=user,
        symbol=symbol,
        defaults={
            "name": name or symbol,
            "asset_type": asset_type,
            "category": category,
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
        existing = Position.objects.filter(portfolio=portfolio, asset=asset).first()
        old_qty = existing.quantity if existing else None
        position, created = Position.objects.update_or_create(
            portfolio=portfolio,
            asset=asset,
            defaults={"quantity": holding.quantity},
        )
        if created or old_qty != holding.quantity:
            positions_updated += 1

    for trade in trades:
        asset_type = trade.asset_type or AssetType.CRYPTO
        asset = _get_or_create_asset(
            user,
            trade.symbol,
            asset_type=asset_type,
        )
        tx_type = trade.transaction_type or _map_trade_type(trade.side)
        price = trade.price_eur if trade.price_eur is not None else Decimal(0)
        total = (
            trade.total_eur
            if trade.total_eur is not None
            else trade.quantity * price
        )
        tx_hash = _transaction_hash(
            platform=connection.platform,
            external_id=trade.external_id or "",
            symbol=trade.symbol,
            side=tx_type,
            quantity=trade.quantity,
            price=price,
            occurred_at=trade.occurred_at,
        )
        _, created = Transaction.objects.get_or_create(
            portfolio=portfolio,
            transaction_hash=tx_hash,
            defaults={
                "asset": asset,
                "transaction_type": tx_type,
                "quantity": trade.quantity,
                "price_eur": price if price else None,
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
        if (
            connection.platform == PlatformType.DEGIRO
            and connection.connection_method == ConnectionMethod.CSV
        ):
            raise PlatformAdapterError(
                "DEGIRO wordt via CSV bijgewerkt. Upload een nieuw exportbestand."
            )
        raise PlatformAdapterError(f"Platform {connection.platform} wordt nog niet ondersteund.")
    return adapter_cls(connection)


def _complete_csv_connection_sync(connection, sync_job) -> None:
    """CSV-koppelingen hebben geen API — status op basis van reeds geïmporteerde data."""
    portfolio = connection.portfolio
    positions_count = portfolio.positions.count()
    transactions_count = portfolio.transactions.filter(
        source_platform=connection.platform,
    ).count()

    sync_job.positions_synced = positions_count
    sync_job.transactions_synced = transactions_count
    sync_job.status = SyncStatus.SUCCESS
    sync_job.error_message = ""

    connection.status = SyncStatus.SUCCESS
    connection.last_synced_at = timezone.now()
    connection.last_error = ""
    connection.save(update_fields=["status", "last_synced_at", "last_error", "updated_at"])


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
        if connection.connection_method == ConnectionMethod.CSV and not connection.is_demo:
            _complete_csv_connection_sync(connection, sync_job)
            return

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
