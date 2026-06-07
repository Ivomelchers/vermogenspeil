"""Gedeelde constanten voor kolommapping (AI, learned, sanity)."""

from apps.integrations.csv.headers import normalize_header

DESCRIPTION_FORBIDDEN_HEADERS = frozenset(
    {
        "exec venue",
        "execution venue",
        "venue",
        "market",
        "mic",
        "exchange",
        "exchange code",
        "uitvoeringsplaats",
        "fx",
        "fx fee",
        "fx ccy",
        "currency",
        "ref",
        "order id",
        "local val",
        "local value",
        "value in eur",
        "waarde eur",
    }
)

CANONICAL_FIELDS = (
    "date",
    "time",
    "product",
    "isin",
    "description",
    "quantity",
    "price",
    "fee",
    "total",
    "currency",
    "local_value",
    "exchange_rate",
    "order_id",
)

CRITICAL_CANONICALS = frozenset({"date", "total"})


def is_forbidden_description_header(header: str) -> bool:
    return normalize_header(header) in DESCRIPTION_FORBIDDEN_HEADERS
