import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone


class DegiroParseError(ValueError):
    pass


@dataclass
class DegiroRow:
    external_id: str
    symbol: str
    name: str
    side: str
    quantity: Decimal
    price_eur: Decimal
    fee_eur: Decimal
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


def _side_from_description(description: str) -> str | None:
    text = (description or "").lower()
    if any(word in text for word in ("koop", "buy", "purchase")):
        return "buy"
    if any(word in text for word in ("verkoop", "sell", "sale")):
        return "sell"
    return None


def _row_hash(parts: list[str]) -> str:
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


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

    missing = [name for name, col_val in [
        ("Date", date_col),
        ("Product", product_col),
        ("Quantity", qty_col),
        ("Price", price_col),
    ] if not col_val]
    if missing:
        raise DegiroParseError(f"Ontbrekende kolommen: {', '.join(missing)}")

    rows: list[DegiroRow] = []
    for index, raw in enumerate(reader, start=2):
        description = raw.get(desc_col or "", "") if desc_col else ""
        side = _side_from_description(description)
        if not side:
            continue

        try:
            quantity = abs(_parse_decimal(raw[qty_col]))
            price = abs(_parse_decimal(raw[price_col]))
        except DegiroParseError as exc:
            raise DegiroParseError(f"Regel {index}: {exc}") from exc

        if quantity <= 0 or price <= 0:
            continue

        product = (raw.get(product_col) or "").strip()
        isin = (raw.get(isin_col) or "").strip() if isin_col else ""
        symbol = isin[:12] if isin else product[:32] or f"ROW{index}"
        fee = _parse_decimal(raw[fee_col]) if fee_col else Decimal(0)
        occurred_at = _parse_date(raw[date_col], raw.get(time_col or "", "") if time_col else "")

        tx_hash = _row_hash(
            [
                "degiro",
                symbol,
                side,
                str(quantity),
                str(price),
                occurred_at.isoformat(),
            ]
        )

        rows.append(
            DegiroRow(
                external_id=f"degiro-csv-{tx_hash[:16]}",
                symbol=symbol,
                name=product or symbol,
                side=side,
                quantity=quantity,
                price_eur=price,
                fee_eur=abs(fee),
                occurred_at=occurred_at,
                transaction_hash=tx_hash,
            )
        )

    if not rows:
        raise DegiroParseError("Geen koop/verkoop-regels gevonden in CSV.")

    return rows
