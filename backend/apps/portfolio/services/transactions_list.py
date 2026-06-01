from django.db.models import QuerySet

from apps.portfolio.models import Transaction

ALLOWED_SORT_FIELDS = {
    "occurred_at": "occurred_at",
    "symbol": "asset__symbol",
    "transaction_type": "transaction_type",
    "source_platform": "source_platform",
    "quantity": "quantity",
    "price_eur": "price_eur",
}

DEFAULT_PAGE_SIZE = 25
MAX_PAGE_SIZE = 100


def parse_page(value: str | None, *, default: int = 1) -> int:
    try:
        page = int(value or default)
    except (TypeError, ValueError):
        return default
    return max(1, page)


def parse_page_size(value: str | None) -> int:
    try:
        size = int(value or DEFAULT_PAGE_SIZE)
    except (TypeError, ValueError):
        return DEFAULT_PAGE_SIZE
    return min(max(1, size), MAX_PAGE_SIZE)


def filter_transactions(
    queryset: QuerySet[Transaction],
    *,
    platform: str | None = None,
    transaction_type: str | None = None,
    symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> QuerySet[Transaction]:
    if platform:
        queryset = queryset.filter(source_platform=platform.strip().lower())
    if transaction_type:
        queryset = queryset.filter(transaction_type=transaction_type.strip().lower())
    if symbol:
        queryset = queryset.filter(asset__symbol__icontains=symbol.strip())
    if date_from:
        queryset = queryset.filter(occurred_at__date__gte=date_from.strip())
    if date_to:
        queryset = queryset.filter(occurred_at__date__lte=date_to.strip())
    return queryset


def sort_transactions(
    queryset: QuerySet[Transaction],
    *,
    sort: str | None = None,
    order: str | None = None,
) -> QuerySet[Transaction]:
    field_key = (sort or "occurred_at").strip().lower()
    db_field = ALLOWED_SORT_FIELDS.get(field_key, "occurred_at")
    direction = "-" if (order or "desc").strip().lower() == "desc" else ""
    return queryset.order_by(f"{direction}{db_field}", "-id")


def paginate_queryset(queryset: QuerySet[Transaction], *, page: int, page_size: int) -> dict:
    total = queryset.count()
    total_pages = max(1, (total + page_size - 1) // page_size) if total else 1
    page = min(page, total_pages) if total else 1
    offset = (page - 1) * page_size
    items = list(queryset[offset : offset + page_size])
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }


def list_portfolio_transactions(
    portfolio,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    sort: str | None = None,
    order: str | None = None,
    platform: str | None = None,
    transaction_type: str | None = None,
    symbol: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
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
    return paginate_queryset(queryset, page=page, page_size=page_size)


def transaction_filter_options(portfolio) -> dict:
    platforms = (
        portfolio.transactions.exclude(source_platform="")
        .values_list("source_platform", flat=True)
        .distinct()
        .order_by("source_platform")
    )
    types = (
        portfolio.transactions.values_list("transaction_type", flat=True)
        .distinct()
        .order_by("transaction_type")
    )
    symbols = (
        portfolio.transactions.select_related("asset")
        .values_list("asset__symbol", flat=True)
        .distinct()
        .order_by("asset__symbol")
    )
    return {
        "platforms": list(platforms),
        "transaction_types": list(types),
        "symbols": list(symbols),
    }
