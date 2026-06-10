"""Gedeelde importlogica voor standaard CSV-rijen (brokers + exchanges)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.integrations.csv.base import CsvParseResult
from apps.integrations.models import ConnectionMethod, PlatformConnection, SyncStatus
from apps.integrations.services.import_batches import (
    create_import_batch,
    finalize_import_batch,
    rebuild_portfolio_positions,
)
from apps.portfolio.models import Asset, AssetType, Transaction, VermogensCategorie
from apps.portfolio.services import get_or_create_default_portfolio
from apps.portfolio.services.position_costs import recompute_position_average_costs
from apps.pricing.isin import looks_like_isin
from apps.pricing.services.instrument_service import asset_type_for_isin


@dataclass
class StandardCsvRow:
    external_id: str
    symbol: str
    name: str
    transaction_type: str
    quantity: Decimal
    price_eur: Decimal | None
    fee_eur: Decimal
    total_eur: Decimal
    occurred_at: datetime
    transaction_hash: str
    asset_type: str = ""


def asset_type_for_symbol(symbol: str, transaction_type: str, *, default_crypto: bool = False) -> str:
    from apps.portfolio.models import TransactionType

    if symbol.upper() in {"EUR", "CASH"} or transaction_type in (
        TransactionType.DEPOSIT,
        TransactionType.WITHDRAWAL,
    ):
        return AssetType.CASH
    if looks_like_isin(symbol):
        hinted = asset_type_for_isin(symbol)
        if hinted:
            return hinted
        return AssetType.ETF if symbol.upper().startswith("IE") else AssetType.STOCK
    if default_crypto:
        return AssetType.CRYPTO
    return AssetType.STOCK


def category_for_asset_type(asset_type: str) -> str:
    if asset_type == AssetType.CASH:
        return VermogensCategorie.BANKTEGOED
    return VermogensCategorie.BELEGGING


@transaction.atomic
def import_standard_csv_for_user(
    user,
    *,
    platform: str,
    platform_display: str,
    label: str,
    parse_result: CsvParseResult,
    source_filename: str = "",
    column_mapping: dict | None = None,
    ai_used: bool = False,
    default_crypto: bool = False,
) -> dict:
    rows: list[StandardCsvRow] = parse_result.rows
    portfolio = get_or_create_default_portfolio(user)

    connection, _ = PlatformConnection.objects.update_or_create(
        user=user,
        platform=platform,
        label=label,
        defaults={
            "portfolio": portfolio,
            "connection_method": ConnectionMethod.CSV,
            "is_active": True,
            "is_demo": False,
            "status": SyncStatus.RUNNING,
            "last_error": "",
        },
    )
    connection.connection_method = ConnectionMethod.CSV
    connection.is_demo = False
    connection.last_error = ""
    connection.save()

    import_batch = create_import_batch(
        connection,
        source_label=label,
        source_filename=source_filename,
        ai_used=ai_used,
        column_mapping=column_mapping or {},
        rows_in_file=parse_result.rows_in_file,
        rows_recognized=len(rows),
    )

    imported = 0
    skipped = 0
    by_type: dict[str, int] = {}
    new_occurred_times = []

    for row in rows:
        asset_type = row.asset_type or asset_type_for_symbol(
            row.symbol,
            row.transaction_type,
            default_crypto=default_crypto,
        )
        asset, created = Asset.objects.get_or_create(
            user=user,
            symbol=row.symbol,
            defaults={
                "name": row.name or row.symbol,
                "asset_type": asset_type,
                "category": category_for_asset_type(asset_type),
            },
        )
        if not created and asset.name in ("", row.symbol) and row.name:
            asset.name = row.name
            asset.save(update_fields=["name", "updated_at"])
        if not created and asset.asset_type == AssetType.OTHER and asset_type != AssetType.OTHER:
            asset.asset_type = asset_type
            asset.save(update_fields=["asset_type", "updated_at"])

        _, created = Transaction.objects.get_or_create(
            portfolio=portfolio,
            transaction_hash=row.transaction_hash,
            defaults={
                "asset": asset,
                "transaction_type": row.transaction_type,
                "quantity": row.quantity,
                "price_eur": row.price_eur,
                "fee_eur": row.fee_eur,
                "total_eur": row.total_eur,
                "occurred_at": row.occurred_at,
                "external_id": row.external_id,
                "source_platform": platform,
                "import_batch": import_batch,
            },
        )
        if created:
            imported += 1
            by_type[row.transaction_type] = by_type.get(row.transaction_type, 0) + 1
            new_occurred_times.append(row.occurred_at)
        else:
            skipped += 1

    finalize_import_batch(
        import_batch,
        transactions_imported=imported,
        transactions_skipped=skipped,
    )

    if ai_used and imported > 0 and column_mapping:
        import_batch.column_mapping = column_mapping
        import_batch.save(update_fields=["column_mapping", "updated_at"])
        from apps.integrations.services.learned_aliases import record_learned_aliases_from_import

        record_learned_aliases_from_import(import_batch)

    rebuild_portfolio_positions(portfolio)
    recompute_position_average_costs(portfolio)

    if new_occurred_times:
        from apps.snapshots.services.recalculate import maybe_recalculate_peildatum_snapshots

        for occurred_at in new_occurred_times:
            maybe_recalculate_peildatum_snapshots(user, occurred_at)

    connection.status = SyncStatus.SUCCESS
    connection.last_synced_at = timezone.now()
    connection.last_error = ""
    connection.save(update_fields=["status", "last_synced_at", "last_error", "updated_at"])

    return {
        "connection_id": connection.id,
        "import_batch_id": import_batch.id,
        "rows_parsed": len(rows),
        "transactions_imported": imported,
        "transactions_skipped": skipped,
        "by_type": by_type,
        "parser_skipped_count": parse_result.rows_skipped,
    }
