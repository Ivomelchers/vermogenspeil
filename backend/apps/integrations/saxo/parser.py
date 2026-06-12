"""Saxo Bank CSV parser."""

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.integrations.csv.base import CsvParseError, CsvParseResult, CsvSkippedRow
from apps.integrations.csv.column_resolution import build_resolver_from_mapping
from apps.integrations.csv.column_schema import build_column_resolver
from apps.integrations.csv.headers import detect_delimiter, normalize_header
from apps.integrations.saxo.column_schema import SAXO_SCHEMA
from apps.portfolio.models import TransactionType


@dataclass
class SaxoRow:
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
    isin: str = ""
    currency: str = "EUR"
    line_number: int = 0


def _parse_decimal(value: str) -> Decimal:
    """Parse decimal value, handling both comma and dot as decimal separator."""
    cleaned = (value or "").strip().replace(",", ".")
    if not cleaned or cleaned == "-":
        return Decimal(0)
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise CsvParseError(f"Ongeldig getal: {value}") from exc


def _parse_date(value: str, time_value: str | None = None) -> datetime:
    """Parse date and optional time."""
    date_part = (value or "").strip()
    time_part = (time_value or "00:00:00").strip()

    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            if fmt in ("%d-%m-%Y", "%Y-%m-%d"):
                parsed = datetime.strptime(date_part, fmt)
            else:
                parsed = datetime.strptime(f"{date_part} {time_part}", fmt)
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            continue

    raise CsvParseError(f"Ongeldige datum: {date_part} {time_part}")


def _row_hash(parts: list[str]) -> str:
    """Generate transaction hash for deduplication."""
    raw = "|".join(parts)
    return hashlib.sha256(raw.encode()).hexdigest()


def _normalize_transaction_type(raw_type: str) -> str:
    """Normalize Saxo transaction type to our standard types."""
    raw = (raw_type or "").lower().strip()

    if "buy" in raw or "køb" in raw or "kauf" in raw:
        return TransactionType.BUY
    elif "sell" in raw or "salg" in raw or "verkauf" in raw or "short" in raw:
        return TransactionType.SELL
    elif "dividend" in raw or "distribution" in raw or "udbytte" in raw:
        return TransactionType.DIVIDEND
    elif "deposit" in raw or "indskud" in raw:
        return TransactionType.DEPOSIT
    elif "withdrawal" in raw or "hæv" in raw or "auszahlung" in raw:
        return TransactionType.WITHDRAWAL
    elif "fee" in raw or "gebyr" in raw or "kosten" in raw or "commission" in raw:
        return TransactionType.FEE
    elif "interest" in raw or "rente" in raw:
        return TransactionType.DIVIDEND  # Treat interest as dividend for now
    else:
        return TransactionType.UNKNOWN


def parse_saxo_csv(csv_content: str, column_mapping: dict | None = None) -> CsvParseResult:
    """Parse Saxo Bank CSV export."""
    if not csv_content.strip():
        raise CsvParseError("CSV-bestand is leeg.")

    skipped_rows = []
    rows = []

    try:
        # Detect delimiter
        delimiter = detect_delimiter(csv_content)

        # Parse CSV
        reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        if not reader.fieldnames:
            raise CsvParseError("CSV heeft geen kolomkoppen.")

        # Build header map
        header_map = {normalize_header(name): name for name in reader.fieldnames if name}
        normalized_headers = set(header_map.keys())

        # Build column resolver
        if column_mapping:
            resolver = build_resolver_from_mapping(SAXO_SCHEMA, header_map, column_mapping)
        else:
            resolver = build_column_resolver(SAXO_SCHEMA, header_map)

        date_col = resolver.get("date")
        time_col = resolver.get("time")
        symbol_col = resolver.get("symbol")
        type_col = resolver.get("type")
        qty_col = resolver.get("quantity")
        price_col = resolver.get("price")
        total_col = resolver.get("total")
        fee_col = resolver.get("fees")
        isin_col = resolver.get("isin")
        desc_col = resolver.get("description")
        currency_col = resolver.get("currency")

        for index, raw_row in enumerate(reader, start=2):
            try:
                # Skip empty rows
                if not any((v or "").strip() for v in raw_row.values()):
                    continue

                # Get column values
                date_val = (raw_row.get(date_col or "") or "").strip() if date_col else ""
                time_val = (raw_row.get(time_col or "") or "").strip() if time_col else ""
                symbol = (raw_row.get(symbol_col or "") or "").strip() if symbol_col else ""
                transaction_type_raw = (raw_row.get(type_col or "") or "").strip() if type_col else ""
                quantity_raw = (raw_row.get(qty_col or "") or "").strip() if qty_col else ""
                price_raw = (raw_row.get(price_col or "") or "").strip() if price_col else ""
                total_raw = (raw_row.get(total_col or "") or "").strip() if total_col else ""
                fee_raw = (raw_row.get(fee_col or "") or "").strip() if fee_col else ""
                isin = (raw_row.get(isin_col or "") or "").strip() if isin_col else ""
                name = (raw_row.get(desc_col or "") or "").strip() if desc_col else symbol
                currency = (raw_row.get(currency_col or "") or "").strip() if currency_col else "EUR"

                if not date_val or not symbol or not transaction_type_raw:
                    skipped_rows.append(
                        CsvSkippedRow(
                            line_number=index,
                            reason="Ontbrekende verplichte kolommen",
                        )
                    )
                    continue

                # Parse values
                occurred_at = _parse_date(date_val, time_val)
                quantity = _parse_decimal(quantity_raw)

                if quantity == 0:
                    skipped_rows.append(
                        CsvSkippedRow(
                            line_number=index,
                            reason="Hoeveelheid is nul",
                        )
                    )
                    continue

                # Price: try total/qty first, else use price column
                if total_raw:
                    total_eur = _parse_decimal(total_raw)
                    if quantity != 0:
                        price_eur = total_eur / quantity
                    else:
                        price_eur = Decimal(0)
                elif price_raw:
                    price_eur = _parse_decimal(price_raw)
                    total_eur = quantity * price_eur
                else:
                    price_eur = None
                    total_eur = Decimal(0)

                fee_eur = _parse_decimal(fee_raw) if fee_raw else Decimal(0)

                # Normalize transaction type
                tx_type = _normalize_transaction_type(transaction_type_raw)

                # Generate hash for deduplication
                hash_parts = [
                    str(occurred_at),
                    str(symbol),
                    str(quantity),
                    str(price_eur or 0),
                ]
                transaction_hash = _row_hash(hash_parts)

                row = SaxoRow(
                    external_id=transaction_hash[:16],  # Use first 16 chars of hash
                    symbol=symbol,
                    name=name,
                    transaction_type=tx_type,
                    quantity=quantity,
                    price_eur=price_eur,
                    fee_eur=fee_eur,
                    total_eur=total_eur,
                    occurred_at=occurred_at,
                    transaction_hash=transaction_hash,
                    isin=isin,
                    currency=currency,
                    line_number=index,
                )
                rows.append(row)

            except CsvParseError as exc:
                skipped_rows.append(
                    CsvSkippedRow(
                        line_number=index,
                        reason=str(exc),
                    )
                )
            except Exception as exc:
                skipped_rows.append(
                    CsvSkippedRow(
                        line_number=index,
                        reason=f"Parseerfout: {exc}",
                    )
                )

    except CsvParseError as exc:
        raise exc

    return CsvParseResult(
        rows=rows,
        rows_in_file=len(rows) + len(skipped_rows),
        skipped=skipped_rows,
    )
