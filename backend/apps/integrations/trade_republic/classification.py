"""Map Trade Republic Type-kolom naar TransactionType."""

from decimal import Decimal

from apps.portfolio.models import TransactionType

CASH_SYMBOL = "EUR"

_TYPE_MAP: dict[str, str] = {
    "purchase": TransactionType.BUY,
    "sale": TransactionType.SELL,
    "dividends": TransactionType.DIVIDEND,
    "deposit": TransactionType.DEPOSIT,
    "withdrawal": TransactionType.WITHDRAWAL,
    "interest payout": TransactionType.OTHER,
    "round up": TransactionType.BUY,
    "saveback": TransactionType.BUY,
}


def classify_trade_republic_type(tx_type: str) -> str | None:
    text = (tx_type or "").lower().strip()
    if not text:
        return None
    return _TYPE_MAP.get(text)


def is_cash_row(transaction_type: str) -> bool:
    return transaction_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL)


def resolve_symbol(
    *,
    transaction_type: str,
    instrument: str,
    name: str,
    line_number: int,
) -> str:
    if is_cash_row(transaction_type):
        return CASH_SYMBOL
    instrument_clean = (instrument or "").strip()
    if instrument_clean:
        return instrument_clean[:12]
    name_clean = (name or "").strip()
    if name_clean:
        return name_clean[:32]
    return f"ROW{line_number}"


def amounts_for_row(
    transaction_type: str,
    *,
    shares_raw: Decimal,
    rate_raw: Decimal,
    debit_raw: Decimal,
    credit_raw: Decimal,
    commission_raw: Decimal,
) -> tuple[Decimal, Decimal | None, Decimal, Decimal] | None:
    total = credit_raw if credit_raw != 0 else debit_raw
    total = abs(total)
    if total == 0:
        return None

    fee = abs(commission_raw)
    needs_shares = transaction_type in (TransactionType.BUY, TransactionType.SELL)
    if shares_raw != 0:
        quantity = abs(shares_raw)
    elif needs_shares:
        quantity = Decimal(1)
    else:
        quantity = Decimal(0)

    price_eur: Decimal | None = None
    if rate_raw > 0:
        price_eur = rate_raw
    elif quantity > 0 and total > 0:
        price_eur = (total / quantity).quantize(Decimal("0.000001"))

    return quantity, price_eur, total, fee
