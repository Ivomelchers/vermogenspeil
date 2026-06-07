from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from apps.integrations.csv.base import CsvParseError, CsvParseResult
from apps.integrations.degiro.parser import parse_degiro_csv

DegiroParseError = CsvParseError
from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformType, SyncStatus
from apps.integrations.degiro.classification import CASH_SYMBOL
from apps.integrations.services.import_batches import (
    create_import_batch,
    finalize_import_batch,
    rebuild_portfolio_positions,
)
from apps.portfolio.models import (
    Asset,
    AssetType,
    Transaction,
    TransactionType,
    VermogensCategorie,
)
from apps.portfolio.services import get_or_create_default_portfolio
from apps.portfolio.services.position_costs import recompute_position_average_costs
from apps.pricing.isin import looks_like_isin
from apps.pricing.services.instrument_service import asset_type_for_isin


def _asset_type_for_symbol(symbol: str, transaction_type: str) -> str:
    if symbol == CASH_SYMBOL or transaction_type in (
        TransactionType.DEPOSIT,
        TransactionType.WITHDRAWAL,
    ):
        return AssetType.CASH
    if looks_like_isin(symbol):
        hinted = asset_type_for_isin(symbol)
        if hinted:
            return hinted
        return AssetType.ETF if symbol.upper().startswith("IE") else AssetType.STOCK
    return AssetType.STOCK


def _category_for_asset_type(asset_type: str) -> str:
    if asset_type == AssetType.CASH:
        return VermogensCategorie.BANKTEGOED
    return VermogensCategorie.BELEGGING


@transaction.atomic
def import_degiro_csv_for_user(
    user,
    file_content: str,
    *,
    label: str = "DEGIRO (CSV)",
    parse_result: CsvParseResult | None = None,
    source_filename: str = "",
    column_mapping: dict | None = None,
    ai_used: bool = False,
) -> dict:
    result = parse_result or parse_degiro_csv(
        file_content,
        column_mapping=column_mapping or None,
    )
    rows = result.rows
    portfolio = get_or_create_default_portfolio(user)

    connection, _ = PlatformConnection.objects.update_or_create(
        user=user,
        platform=PlatformType.DEGIRO,
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
        rows_in_file=result.rows_in_file,
        rows_recognized=len(rows),
    )

    imported = 0
    skipped = 0
    by_type: dict[str, int] = {}
    new_occurred_times = []

    for row in rows:
        asset_type = _asset_type_for_symbol(row.symbol, row.transaction_type)
        asset, created = Asset.objects.get_or_create(
            user=user,
            symbol=row.symbol,
            defaults={
                "name": row.name,
                "asset_type": asset_type,
                "category": _category_for_asset_type(asset_type),
            },
        )
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
                "source_platform": PlatformType.DEGIRO,
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
        "parser_skipped_count": result.rows_skipped,
    }
