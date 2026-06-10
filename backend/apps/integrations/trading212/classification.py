"""Map Trading 212 Action-kolom naar TransactionType."""

from decimal import Decimal

from apps.portfolio.models import TransactionType

CASH_SYMBOL = "EUR"

_SKIP_ACTIONS: frozenset[str] = frozenset(
    {
        "currency conversion",
        "card top-up",
        "card top up",
    }
)

_ACTION_MAP: tuple[tuple[tuple[str, ...], str], ...] = (
    (("market buy", "limit buy"), TransactionType.BUY),
    (("market sell", "limit sell"), TransactionType.SELL),
    (("dividend (dividend)", "dividend"), TransactionType.DIVIDEND),
    (("deposit",), TransactionType.DEPOSIT),
    (("interest on cash", "share lending interest"), TransactionType.OTHER),
)


def classify_trading212_action(action: str) -> str | None:
    text = (action or "").lower().strip()
    if not text:
        return None
    if text in _SKIP_ACTIONS:
        return None
    for keywords, tx_type in _ACTION_MAP:
        if any(keyword in text for keyword in keywords):
            return tx_type
    return None


def is_cash_row(transaction_type: str) -> bool:
    return transaction_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL)


def resolve_symbol(
    *,
    transaction_type: str,
    isin: str,
    ticker: str,
    name: str,
    line_number: int,
) -> str:
    if is_cash_row(transaction_type):
        return CASH_SYMBOL
    isin_clean = (isin or "").strip()
    if isin_clean:
        return isin_clean[:12]
    ticker_clean = (ticker or "").strip()
    if ticker_clean:
        return ticker_clean[:32]
    name_clean = (name or "").strip()
    if name_clean:
        return name_clean[:32]
    return f"ROW{line_number}"


def amounts_for_row(
    transaction_type: str,
    *,
    quantity_raw: Decimal,
    price_raw: Decimal,
    total_raw: Decimal,
) -> tuple[Decimal, Decimal | None, Decimal] | None:
    total = abs(total_raw)
    if total == 0:
        return None

    needs_shares = transaction_type in (TransactionType.BUY, TransactionType.SELL)
    if quantity_raw != 0:
        quantity = abs(quantity_raw)
    elif needs_shares:
        quantity = Decimal(1)
    else:
        quantity = Decimal(0)

    price_eur: Decimal | None = None
    if price_raw > 0:
        price_eur = price_raw
    elif quantity > 0 and total > 0:
        price_eur = (total / quantity).quantize(Decimal("0.000001"))

    return quantity, price_eur, total
