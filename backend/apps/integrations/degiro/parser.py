import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.integrations.degiro.classification import CASH_SYMBOL, classify_degiro_description, is_cash_row
from apps.portfolio.models import TransactionType


class DegiroParseError(ValueError):
    pass


@dataclass
class DegiroRow:
    external_id: str
    symbol: str
    name: str
    transaction_type: str
    quantity: Decimal
    price_eur: Decimal | None
    fee_eur: Decimal
    total_eur: Decimal
    occurred_at: datetime
    transaction_hash: str


def _parse_decimal(value: str) -> Decimal:
    cleaned = (value or "").strip().replace(",", ".")
    if not cleaned or cleaned == "-":
        return Decimal(0)
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise DegiroParseError(f"Ongeldig getal: {value}") from exc


def _parse_date(value: str, time_value: str) -> datetime:
    date_part = (value or "").strip()
    time_part = (time_value or "00:00:00").strip()
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y"):
        try:
            if fmt == "%d-%m-%Y":
                parsed = datetime.strptime(date_part, fmt)
            else:
                parsed = datetime.strptime(f"{date_part} {time_part}", fmt)
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            continue
    raise DegiroParseError(f"Ongeldige datum: {value} {time_value}")


def _normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def _row_hash(parts: list[str]) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _resolve_symbol(product: str, isin: str, transaction_type: str, index: int) -> str:
    if is_cash_row(transaction_type, product, isin):
        return CASH_SYMBOL
    isin_clean = (isin or "").strip()
    if isin_clean:
        return isin_clean[:12]
    product_clean = (product or "").strip()
    if product_clean:
        return product_clean[:32]
    return f"ROW{index}"


def _amounts_for_row(
    transaction_type: str,
    *,
    quantity_raw: Decimal,
    price_raw: Decimal,
    total_raw: Decimal,
    fee_raw: Decimal,
) -> tuple[Decimal, Decimal | None, Decimal] | None:
    """Return (quantity, price_eur, total_eur) or None to skip row."""
    if transaction_type in (TransactionType.BUY, TransactionType.SELL):
        quantity = abs(quantity_raw)
        price = abs(price_raw)
        if quantity <= 0 or price <= 0:
            return None
        total = quantity * price
        return quantity, price, total

    if total_raw != 0:
        total = total_raw
    else:
        total = quantity_raw * price_raw
    if total == 0:
        return None
    if transaction_type in (TransactionType.DEPOSIT, TransactionType.DIVIDEND):
        total = abs(total)
    quantity = abs(quantity_raw) if quantity_raw > 0 else Decimal(1)
    return quantity, None, total


def parse_degiro_csv(content: str) -> list[DegiroRow]:
    """Parse DEGIRO Transactions-export (komma of puntkomma)."""
    if not content.strip():
        raise DegiroParseError("CSV-bestand is leeg.")

    sample = content[:2048]
    delimiter = ";" if sample.count(";") > sample.count(",") else ","

    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        raise DegiroParseError("CSV heeft geen kolomkoppen.")

    header_map = {_normalize_header(name): name for name in reader.fieldnames if name}

    def col(*candidates: str) -> str | None:
        for candidate in candidates:
            key = _normalize_header(candidate)
            if key in header_map:
                return header_map[key]
        return None

    date_col = col("date", "datum")
    time_col = col("time", "tijd")
    product_col = col("product")
    isin_col = col("isin")
    desc_col = col("description", "omschrijving", "type")
    qty_col = col("quantity", "aantal")
    price_col = col("price", "koers")
    fee_col = col("transaction costs", "transactiekosten", "kosten")
    total_col = col("total", "totaal", "value")

    if not date_col:
        raise DegiroParseError("Ontbrekende kolom: Date")

    rows: list[DegiroRow] = []
    unknown_descriptions: set[str] = set()

    for index, raw in enumerate(reader, start=2):
        description = raw.get(desc_col or "", "") if desc_col else ""
        transaction_type = classify_degiro_description(description)
        if not transaction_type:
            if description.strip():
                unknown_descriptions.add(description.strip())
            continue

        try:
            quantity_raw = _parse_decimal(raw[qty_col]) if qty_col else Decimal(0)
            price_raw = _parse_decimal(raw[price_col]) if price_col else Decimal(0)
            total_raw = _parse_decimal(raw[total_col]) if total_col else Decimal(0)
            fee = abs(_parse_decimal(raw[fee_col])) if fee_col else Decimal(0)
        except DegiroParseError as exc:
            raise DegiroParseError(f"Regel {index}: {exc}") from exc

        amounts = _amounts_for_row(
            transaction_type,
            quantity_raw=quantity_raw,
            price_raw=price_raw,
            total_raw=total_raw,
            fee_raw=fee,
        )
        if not amounts:
            continue

        quantity, price_eur, total_eur = amounts
        product = (raw.get(product_col) or "").strip() if product_col else ""
        isin = (raw.get(isin_col) or "").strip() if isin_col else ""
        symbol = _resolve_symbol(product, isin, transaction_type, index)
        name = product or symbol
        occurred_at = _parse_date(raw[date_col], raw.get(time_col or "", "") if time_col else "")

        tx_hash = _row_hash(
            [
                "degiro",
                symbol,
                transaction_type,
                str(quantity),
                str(price_eur or ""),
                str(total_eur),
                occurred_at.isoformat(),
                description,
            ]
        )

        rows.append(
            DegiroRow(
                external_id=f"degiro-csv-{tx_hash[:16]}",
                symbol=symbol,
                name=name,
                transaction_type=transaction_type,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=fee,
                total_eur=total_eur,
                occurred_at=occurred_at,
                transaction_hash=tx_hash,
            )
        )

    if not rows:
        hint = ""
        if unknown_descriptions:
            hint = f" Onbekende omschrijvingen: {', '.join(sorted(unknown_descriptions)[:5])}."
        raise DegiroParseError(
            f"Geen herkende transacties in CSV.{hint} "
            "Ondersteund: koop, verkoop, dividend, dividendbelasting, storting, opname, "
            "kosten, rente, valuta en overige DEGIRO-regels."
        )

    return rows
