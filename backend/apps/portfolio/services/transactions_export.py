"""CSV-export transacties (FSD §7)."""

import csv
import io

from apps.portfolio.services.transactions_list import filter_transactions, sort_transactions

CSV_HEADERS = [
    "datum",
    "symbool",
    "naam",
    "type",
    "platform",
    "aantal",
    "prijs_eur",
    "kosten_eur",
    "totaal_eur",
    "notities",
]


def build_transactions_csv(
    portfolio,
    *,
    sort: str | None = None,
    order: str | None = None,
    platform: str | None = None,
    transaction_type: str | None = None,
    symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> str:
    queryset = portfolio.transactions.select_related("asset")
    queryset = filter_transactions(
        queryset,
        platform=platform,
        transaction_type=transaction_type,
        symbol=symbol,
        date_from=date_from,
        date_to=date_to,
    )
    queryset = sort_transactions(queryset, sort=sort, order=order)

    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(CSV_HEADERS)

    for tx in queryset.iterator():
        occurred = tx.occurred_at.astimezone().strftime("%Y-%m-%d %H:%M")
        writer.writerow(
            [
                occurred,
                tx.asset.symbol,
                tx.asset.name or "",
                tx.get_transaction_type_display(),
                tx.source_platform,
                str(tx.quantity),
                str(tx.price_eur) if tx.price_eur is not None else "",
                str(tx.fee_eur),
                str(tx.total_eur) if tx.total_eur is not None else "",
                tx.notes or "",
            ]
        )

    return buffer.getvalue()
