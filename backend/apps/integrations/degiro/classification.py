"""Map DEGIRO CSV Description-kolom naar TransactionType (of NL-export zonder Description)."""

from decimal import Decimal

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


def classify_degiro_row(
    *,
    description: str,
    quantity: Decimal,
    total: Decimal,
    product: str,
    isin: str,
    fee: Decimal = Decimal(0),
) -> str | None:
    """
    Engelse export: Description-kolom (Koop/Verkoop/Dividend).
    Nederlandse export (2024+): vaak geen Description — gebruik teken van Aantal/Totaal.
    """
    from_description = classify_degiro_description(description)
    if from_description:
        return from_description

    desc_stripped = (description or "").strip()
    product_clean = (product or "").strip()
    isin_clean = (isin or "").strip()

    # NL-export zonder Description-kolom: lege omschrijving.
    if not desc_stripped:
        if not product_clean and not isin_clean:
            if total > 0:
                return TransactionType.DEPOSIT
            if total < 0:
                return TransactionType.WITHDRAWAL
            return None
        if quantity == 0:
            if fee > 0 or (total < 0 and abs(total) <= fee + Decimal("0.01")):
                return TransactionType.FEE
            if total > 0 and isin_clean:
                return TransactionType.DIVIDEND
            if total < 0 and isin_clean:
                return TransactionType.FEE
        if quantity < 0:
            return TransactionType.SELL
        if quantity > 0:
            return TransactionType.BUY
        if total != 0 and not product_clean:
            return TransactionType.FEE
        return None

    # Onbekende omschrijving mét product/ISIN (bv. AI koppelde venue/MIC aan Description).
    if product_clean or isin_clean:
        if quantity < 0:
            return TransactionType.SELL
        if quantity > 0:
            return TransactionType.BUY
        if total != 0:
            return TransactionType.FEE

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
