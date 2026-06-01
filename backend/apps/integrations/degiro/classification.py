"""Map DEGIRO CSV Description-kolom naar TransactionType."""

from apps.portfolio.models import TransactionType

CASH_SYMBOL = "EUR"

# Volgorde telt: specifieker eerst (bijv. dividendbelasting vóór dividend).
_RULES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("dividendbelasting", "dividend tax", "withholding tax", "bronbelasting"), TransactionType.FEE),
    (("verkoop", "sell", "sale"), TransactionType.SELL),
    (("koop", "buy", "purchase"), TransactionType.BUY),
    (("dividend", "coupon"), TransactionType.DIVIDEND),
    (
        (
            "ideal",
            "deposit",
            "storting",
            "bank transfer",
            "overboeking",
            "cash sweep transfer",
            "cash sweep",
        ),
        TransactionType.DEPOSIT,
    ),
    (("withdrawal", "opname", "afschrijving", "terugboeking"), TransactionType.WITHDRAWAL),
    (
        (
            "fee",
            "kosten",
            "provisie",
            "connection fee",
            "degiro fee",
            "flatex fee",
            "corporate action fee",
        ),
        TransactionType.FEE,
    ),
    (("valuta", "currency", "fx credit", "fx debit"), TransactionType.OTHER),
    (("interest", "rente", "flatex interest"), TransactionType.OTHER),
    (
        (
            "corporate action",
            "stock split",
            "merger",
            "spin-off",
            "spinoff",
            "isin change",
            "product wijziging",
        ),
        TransactionType.OTHER,
    ),
)


def classify_degiro_description(description: str) -> str | None:
    text = (description or "").lower().strip()
    if not text:
        return None
    for keywords, tx_type in _RULES:
        if any(keyword in text for keyword in keywords):
            return tx_type
    return None


def is_cash_row(transaction_type: str, product: str, isin: str) -> bool:
    if transaction_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL):
        return True
    if not (product or "").strip() and not (isin or "").strip():
        return transaction_type in (
            TransactionType.DEPOSIT,
            TransactionType.WITHDRAWAL,
            TransactionType.FEE,
            TransactionType.OTHER,
        )
    return False
