"""Import-batches: koppeling transacties ↔ platform/CSV/API-sync + data wissen."""

from __future__ import annotations

import logging
from decimal import Decimal

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformImportBatch
from apps.portfolio.models import Asset, Position, Transaction, TransactionType
from apps.portfolio.models import AssetType
from apps.portfolio.services.position_costs import recompute_position_average_costs

logger = logging.getLogger(__name__)


def rebuild_portfolio_positions(portfolio) -> None:
    """Hertel posities uit alle resterende transacties."""
    Position.objects.filter(portfolio=portfolio).delete()

    totals: dict[int, Decimal] = {}
    for tx in portfolio.transactions.select_related("asset").order_by("occurred_at"):
        if tx.transaction_type in (TransactionType.BUY, TransactionType.SELL):
            qty = tx.quantity if tx.transaction_type != TransactionType.SELL else -tx.quantity
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + qty
        elif tx.transaction_type == TransactionType.DEPOSIT and tx.asset.asset_type == AssetType.CASH:
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + (tx.total_eur or Decimal(0))
        elif tx.transaction_type == TransactionType.WITHDRAWAL and tx.asset.asset_type == AssetType.CASH:
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + (tx.total_eur or Decimal(0))
        elif tx.transaction_type == TransactionType.FEE and tx.asset.asset_type == AssetType.CASH:
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + (tx.total_eur or Decimal(0))

    for asset_id, quantity in totals.items():
        if quantity <= 0:
            continue
        Position.objects.create(
            portfolio=portfolio,
            asset_id=asset_id,
            quantity=quantity,
        )

    recompute_position_average_costs(portfolio)


def _cleanup_orphan_assets(user) -> int:
    """Verwijder assets zonder transacties meer (zelfde user)."""
    orphan_ids = (
        Asset.objects.filter(user=user)
        .annotate(tx_count=Count("transactions"))
        .filter(tx_count=0)
        .values_list("id", flat=True)
    )
    deleted, _ = Asset.objects.filter(id__in=list(orphan_ids)).delete()
    return deleted


def create_import_batch(
    connection: PlatformConnection,
    *,
    source_label: str = "",
    source_filename: str = "",
    sync_job=None,
    ai_used: bool = False,
    column_mapping: dict | None = None,
    rows_in_file: int = 0,
    rows_recognized: int = 0,
) -> PlatformImportBatch:
    return PlatformImportBatch.objects.create(
        user=connection.user,
        connection=connection,
        platform=connection.platform,
        connection_method=connection.connection_method,
        source_label=source_label or connection.display_name,
        source_filename=(source_filename or "")[:255],
        sync_job=sync_job,
        ai_used=ai_used,
        column_mapping=column_mapping or {},
        rows_in_file=rows_in_file,
        rows_recognized=rows_recognized,
    )


def finalize_import_batch(
    batch: PlatformImportBatch,
    *,
    transactions_imported: int,
    transactions_skipped: int = 0,
) -> None:
    batch.transactions_imported = transactions_imported
    batch.transactions_skipped = transactions_skipped
    batch.save(
        update_fields=[
            "transactions_imported",
            "transactions_skipped",
            "updated_at",
        ]
    )


@transaction.atomic
def purge_import_batch(user, batch_id: int) -> dict:
    batch = (
        PlatformImportBatch.objects.filter(user=user, pk=batch_id)
        .select_related("connection", "connection__portfolio")
        .first()
    )
    if not batch:
        raise LookupError("Import niet gevonden.")

    portfolio = batch.connection.portfolio if batch.connection_id else None
    if not portfolio:
        portfolio = user.portfolios.filter(is_default=True).first()

    tx_qs = Transaction.objects.filter(import_batch=batch)
    if portfolio:
        tx_qs = tx_qs.filter(portfolio=portfolio)

    deleted_count, _ = tx_qs.delete()
    batch_id = batch.id
    batch.delete()

    if portfolio:
        rebuild_portfolio_positions(portfolio)
        from apps.snapshots.services.recalculate import maybe_recalculate_peildatum_snapshots

        maybe_recalculate_peildatum_snapshots(user, timezone.now())
    orphans = _cleanup_orphan_assets(user)

    return {
        "import_batch_id": batch_id,
        "transactions_deleted": deleted_count,
        "orphan_assets_deleted": orphans,
    }


@transaction.atomic
def purge_connection_data(user, connection_id: int) -> dict:
    from django.db.models import Q

    connection = (
        PlatformConnection.objects.for_user(user)
        .filter(pk=connection_id)
        .select_related("portfolio")
        .first()
    )
    if not connection:
        raise LookupError("Koppeling niet gevonden.")

    portfolio = connection.portfolio
    batch_ids = list(
        PlatformImportBatch.objects.filter(connection=connection).values_list("id", flat=True)
    )

    batch_filter = Q(import_batch_id__in=batch_ids) if batch_ids else Q(pk__in=[])
    sibling_count = PlatformConnection.objects.for_user(user).filter(
        platform=connection.platform,
        connection_method=connection.connection_method,
    ).count()
    if sibling_count <= 1:
        legacy = Q(import_batch__isnull=True, source_platform=connection.platform)
        tx_filter = batch_filter | legacy
    else:
        tx_filter = batch_filter

    deleted_count, _ = Transaction.objects.filter(portfolio=portfolio).filter(tx_filter).delete()

    PlatformImportBatch.objects.filter(connection=connection).delete()

    rebuild_portfolio_positions(portfolio)
    from apps.snapshots.services.recalculate import maybe_recalculate_peildatum_snapshots

    maybe_recalculate_peildatum_snapshots(user, timezone.now())
    orphans = _cleanup_orphan_assets(user)

    return {
        "connection_id": connection_id,
        "import_batches_deleted": len(batch_ids),
        "transactions_deleted": deleted_count,
        "orphan_assets_deleted": orphans,
    }
