from decimal import Decimal

from django.db import transaction
from django.utils import timezone

from apps.integrations.degiro.parser import DegiroParseError, parse_degiro_csv
from apps.integrations.models import ConnectionMethod, PlatformConnection, PlatformType, SyncStatus
from apps.portfolio.models import Asset, AssetType, Position, Transaction, TransactionType, VermogensCategorie
from apps.portfolio.services import get_or_create_default_portfolio


def _map_side(side: str) -> str:
    return TransactionType.SELL if side == "sell" else TransactionType.BUY


def _asset_type_for_symbol(symbol: str) -> str:
    if len(symbol) == 12 and symbol.isalnum():
        return AssetType.ETF if symbol.startswith("IE") else AssetType.STOCK
    return AssetType.STOCK


@transaction.atomic
def import_degiro_csv_for_user(user, file_content: str, *, label: str = "DEGIRO (CSV)") -> dict:
    rows = parse_degiro_csv(file_content)
    portfolio = get_or_create_default_portfolio(user)

    connection, _ = PlatformConnection.objects.update_or_create(
        user=user,
        platform=PlatformType.DEGIRO,
        label=label,
        defaults={
            "portfolio": portfolio,
            "connection_method": ConnectionMethod.CSV,
            "is_active": True,
            "status": SyncStatus.RUNNING,
        },
    )
    connection.connection_method = ConnectionMethod.CSV
    connection.save()

    imported = 0
    skipped = 0

    for row in rows:
        asset, _ = Asset.objects.get_or_create(
            user=user,
            symbol=row.symbol,
            defaults={
                "name": row.name,
                "asset_type": _asset_type_for_symbol(row.symbol),
                "category": VermogensCategorie.BELEGGING,
            },
        )

        total = row.quantity * row.price_eur
        _, created = Transaction.objects.get_or_create(
            portfolio=portfolio,
            transaction_hash=row.transaction_hash,
            defaults={
                "asset": asset,
                "transaction_type": _map_side(row.side),
                "quantity": row.quantity,
                "price_eur": row.price_eur,
                "fee_eur": row.fee_eur,
                "total_eur": total,
                "occurred_at": row.occurred_at,
                "external_id": row.external_id,
                "source_platform": PlatformType.DEGIRO,
            },
        )
        if created:
            imported += 1
        else:
            skipped += 1

    _rebuild_positions_from_transactions(portfolio)

    connection.status = SyncStatus.SUCCESS
    connection.last_synced_at = timezone.now()
    connection.last_error = ""
    connection.save(update_fields=["status", "last_synced_at", "last_error", "updated_at"])

    return {
        "connection_id": connection.id,
        "rows_parsed": len(rows),
        "transactions_imported": imported,
        "transactions_skipped": skipped,
    }


def _rebuild_positions_from_transactions(portfolio) -> None:
    """Hertel posities op basis van netto aantal per asset."""
    Position.objects.filter(portfolio=portfolio).delete()

    totals: dict[int, Decimal] = {}
    for tx in portfolio.transactions.select_related("asset").order_by("occurred_at"):
        qty = tx.quantity if tx.transaction_type != TransactionType.SELL else -tx.quantity
        totals[tx.asset_id] = totals.get(tx.asset_id, Decimal(0)) + qty

    for asset_id, quantity in totals.items():
        if quantity <= 0:
            continue
        Position.objects.create(
            portfolio=portfolio,
            asset_id=asset_id,
            quantity=quantity,
        )
