from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.integrations.degiro.classification import CASH_SYMBOL
from apps.integrations.csv.base import CsvParseError, CsvParseResult
from apps.integrations.degiro.parser import parse_degiro_csv

DegiroParseError = CsvParseError
from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformType, SyncStatus
from apps.portfolio.models import (
    Asset,
    AssetType,
    Position,
    Transaction,
    TransactionType,
    VermogensCategorie,
)
from apps.portfolio.services import get_or_create_default_portfolio
from apps.portfolio.services.position_costs import recompute_position_average_costs


def _asset_type_for_symbol(symbol: str, transaction_type: str) -> str:
    if symbol == CASH_SYMBOL or transaction_type in (
        TransactionType.DEPOSIT,
        TransactionType.WITHDRAWAL,
    ):
        return AssetType.CASH
    if len(symbol) == 12 and symbol.isalnum():
        return AssetType.ETF if symbol.startswith("IE") else AssetType.STOCK
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
) -> dict:
    result = parse_result or parse_degiro_csv(file_content)
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

    imported = 0
    skipped = 0
    by_type: dict[str, int] = {}
    new_occurred_times = []

    for row in rows:
        asset_type = _asset_type_for_symbol(row.symbol, row.transaction_type)
        asset, _ = Asset.objects.get_or_create(
            user=user,
            symbol=row.symbol,
            defaults={
                "name": row.name,
                "asset_type": asset_type,
                "category": _category_for_asset_type(asset_type),
            },
        )

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
            },
        )
        if created:
            imported += 1
            by_type[row.transaction_type] = by_type.get(row.transaction_type, 0) + 1
            new_occurred_times.append(row.occurred_at)
        else:
            skipped += 1

    _rebuild_positions_from_transactions(portfolio)
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
        "rows_parsed": len(rows),
        "transactions_imported": imported,
        "transactions_skipped": skipped,
        "by_type": by_type,
        "parser_skipped_count": result.rows_skipped,
    }


def _rebuild_positions_from_transactions(portfolio) -> None:
    """Hertel posities: effecten via koop/verkoop, cash via stortingen/opnames."""
    Position.objects.filter(portfolio=portfolio).delete()

    totals: dict[int, Decimal] = {}
    for tx in portfolio.transactions.select_related("asset").order_by("occurred_at"):
        if tx.transaction_type in (TransactionType.BUY, TransactionType.SELL):
            qty = tx.quantity if tx.transaction_type != TransactionType.SELL else -tx.quantity
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + qty
        elif tx.transaction_type == TransactionType.DEPOSIT and tx.asset.asset_type == AssetType.CASH:
            amount = tx.total_eur or Decimal(0)
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + amount
        elif tx.transaction_type == TransactionType.WITHDRAWAL and tx.asset.asset_type == AssetType.CASH:
            amount = tx.total_eur or Decimal(0)
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + amount
        elif tx.transaction_type == TransactionType.FEE and tx.asset.asset_type == AssetType.CASH:
            amount = tx.total_eur or Decimal(0)
            totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + amount

    for asset_id, quantity in totals.items():
        if quantity <= 0:
            continue
        Position.objects.create(
            portfolio=portfolio,
            asset_id=asset_id,
            quantity=quantity,
        )
