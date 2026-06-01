from collections import defaultdict

from django.db import transaction
from django.db.models import Count

from apps.portfolio.models import Asset, Transaction
from apps.portfolio.services.manual import _rebuild_position


@transaction.atomic
def dedupe_portfolio_transactions(portfolio) -> dict:
    """Verwijder dubbele transacties; behoud de oudste per external_id of hash."""
    removed = 0

    by_external: dict[tuple[str, str], list[int]] = defaultdict(list)
    for tx_id, platform, ext in (
        portfolio.transactions.exclude(external_id="")
        .values_list("id", "source_platform", "external_id")
        .order_by("id")
    ):
        key = (platform, ext.strip())
        by_external[key].append(tx_id)

    for ids in by_external.values():
        if len(ids) > 1:
            Transaction.objects.filter(pk__in=ids[1:]).delete()
            removed += len(ids) - 1

    dup_hashes = (
        portfolio.transactions.values("transaction_hash")
        .annotate(c=Count("id"))
        .filter(c__gt=1)
    )
    for row in dup_hashes:
        ids = list(
            portfolio.transactions.filter(transaction_hash=row["transaction_hash"])
            .order_by("id")
            .values_list("id", flat=True)
        )
        if len(ids) > 1:
            Transaction.objects.filter(pk__in=ids[1:]).delete()
            removed += len(ids) - 1

    assets_touched = set(
        portfolio.transactions.values_list("asset_id", flat=True).distinct()
    )
    for asset_id in assets_touched:
        asset = Asset.objects.filter(pk=asset_id).first()
        if asset:
            _rebuild_position(portfolio, asset)

    return {"removed": removed, "remaining": portfolio.transactions.count()}
