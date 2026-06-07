import csv
import hashlib
import io
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.integrations.csv.base import CsvParseError, CsvParseResult, CsvSkippedRow
from apps.integrations.csv.column_resolution import build_resolver_from_mapping
from apps.integrations.csv.column_schema import build_column_resolver
from apps.integrations.csv.headers import detect_delimiter, normalize_header
from apps.integrations.degiro.ai_description import (
    DescriptionRowContext,
    ai_description_classification_enabled,
    classify_unknown_descriptions_with_ai,
)
from apps.integrations.degiro.classification import (
    CASH_SYMBOL,
    classify_degiro_row,
    is_cash_row,
)
from apps.integrations.degiro.column_prefs import prefer_settlement_total_column
from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA
from apps.integrations.degiro.fingerprint import degiro_fingerprint_score, degiro_missing_required
from apps.portfolio.models import TransactionType

# Backwards compatibility
DegiroParseError = CsvParseError


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
    mic: str = ""
    description: str = ""
    currency: str = ""
    line_number: int = 0


def _parse_decimal(value: str) -> Decimal:
    cleaned = (value or "").strip().replace(",", ".")
    if not cleaned or cleaned == "-":
        return Decimal(0)
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise CsvParseError(f"Ongeldig getal: {value}") from exc


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
    raise CsvParseError(f"Ongeldige datum: {value} {time_value}")


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
    """
    DEGIRO Transactions-CSV: Total is vaak negatief bij uitgaven (koop, kosten, opname).
    Wij slaan total_eur op als positief bedrag (grootte van de transactie).
    """
    total = total_raw
    if total == 0:
        return None
    total = abs(total)
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


def _row_preview(raw: dict, max_len: int = 120) -> str:
    parts = [str(v) for v in raw.values() if v]
    text = ";".join(parts)
    return text[:max_len] + ("…" if len(text) > max_len else "")


def parse_degiro_csv(
    content: str,
    *,
    column_mapping: dict[str, str] | None = None,
) -> CsvParseResult:
    """Parse DEGIRO Transactions-export (komma of puntkomma)."""
    if not content.strip():
        raise CsvParseError("CSV-bestand is leeg.")

    delimiter = detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        raise CsvParseError("CSV heeft geen kolomkoppen.")

    header_map = {_normalize_header(name): name for name in reader.fieldnames if name}
    normalized_headers = set(header_map.keys())

    if column_mapping:
        columns = build_resolver_from_mapping(DEGIRO_SCHEMA, header_map, column_mapping)
        columns = prefer_settlement_total_column(columns, header_map)
        if not columns.get("date") or not columns.get("total"):
            raise CsvParseError(
                "Kolommapping mist verplichte velden (datum of totaal). "
                "Controleer de export of meld nieuwe kolomnamen."
            )
    else:
        score = degiro_fingerprint_score(normalized_headers)
        if score < 0.85:
            missing = degiro_missing_required(normalized_headers)
            raise CsvParseError(
                "Dit is geen herkende DEGIRO-transactie-export. "
                f"Ontbrekende kolommen: {', '.join(missing) or 'onbekend format'}. "
                "Download het bestand 'Transactions' uit uw DEGIRO-account."
            )
        columns = prefer_settlement_total_column(
            build_column_resolver(DEGIRO_SCHEMA, header_map),
            header_map,
        )

    date_col = columns.get("date")
    time_col = columns.get("time")
    product_col = columns.get("product")
    isin_col = columns.get("isin")
    mic_col = columns.get("mic")
    desc_col = columns.get("description")
    qty_col = columns.get("quantity")
    price_col = columns.get("price")
    fee_col = columns.get("fee")
    total_col = columns.get("total")
    order_col = columns.get("order_id")
    currency_col = columns.get("currency")

    rows: list[DegiroRow] = []
    skipped: list[CsvSkippedRow] = []
    data_row_count = 0

    raw_rows: list[tuple[int, dict]] = []
    for index, raw in enumerate(reader, start=2):
        if not any((v or "").strip() for v in raw.values()):
            continue
        raw_rows.append((index, raw))
        data_row_count += 1

    ai_type_by_description: dict[str, str] = {}
    if ai_description_classification_enabled():
        unknown_contexts: list[DescriptionRowContext] = []
        for index, raw in raw_rows:
            description = raw.get(desc_col or "", "") if desc_col else ""
            try:
                quantity_raw = _parse_decimal(raw[qty_col]) if qty_col else Decimal(0)
                total_raw = _parse_decimal(raw[total_col]) if total_col else Decimal(0)
                fee = abs(_parse_decimal(raw[fee_col])) if fee_col else Decimal(0)
            except CsvParseError:
                continue
            if total_raw == 0:
                continue
            product = (raw.get(product_col) or "").strip() if product_col else ""
            isin = (raw.get(isin_col) or "").strip() if isin_col else ""
            tx_type = classify_degiro_row(
                description=description,
                quantity=quantity_raw,
                total=total_raw,
                product=product,
                isin=isin,
                fee=fee,
            )
            if not tx_type and (description or "").strip():
                unknown_contexts.append(
                    DescriptionRowContext(
                        description=description.strip(),
                        quantity=quantity_raw,
                        total=total_raw,
                        fee=fee,
                        has_product=bool(product),
                        has_isin=bool(isin),
                    )
                )
        ai_type_by_description = classify_unknown_descriptions_with_ai(unknown_contexts)

    for index, raw in raw_rows:
        description = raw.get(desc_col or "", "") if desc_col else ""

        try:
            quantity_raw = _parse_decimal(raw[qty_col]) if qty_col else Decimal(0)
            price_raw = _parse_decimal(raw[price_col]) if price_col else Decimal(0)
            total_raw = _parse_decimal(raw[total_col]) if total_col else Decimal(0)
            fee = abs(_parse_decimal(raw[fee_col])) if fee_col else Decimal(0)
        except CsvParseError as exc:
            raise CsvParseError(f"Regel {index}: {exc}") from exc

        product = (raw.get(product_col) or "").strip() if product_col else ""
        isin = (raw.get(isin_col) or "").strip() if isin_col else ""
        mic = _normalize_mic(raw.get(mic_col) or "") if mic_col else ""
        currency = (raw.get(currency_col) or "").strip() if currency_col else ""

        if total_raw == 0:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="zero_amount",
                    description=description.strip(),
                    preview=_row_preview(raw),
                )
            )
            continue

        transaction_type = classify_degiro_row(
            description=description,
            quantity=quantity_raw,
            total=total_raw,
            product=product,
            isin=isin,
            fee=fee,
        )
        if not transaction_type and description.strip():
            transaction_type = ai_type_by_description.get(description.strip())
        if not transaction_type:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="unknown_description",
                    description=description.strip() or f"aantal={quantity_raw}",
                    preview=_row_preview(raw),
                )
            )
            continue

        amounts = _amounts_for_row(
            transaction_type,
            quantity_raw=quantity_raw,
            price_raw=price_raw,
            total_raw=total_raw,
            fee_raw=fee,
        )
        if not amounts:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="zero_amount",
                    description=description.strip(),
                    preview=_row_preview(raw),
                )
            )
            continue

        quantity, price_eur, total_eur = amounts
        symbol = _resolve_symbol(product, isin, transaction_type, index)
        name = product or symbol
        occurred_at = _parse_date(raw[date_col], raw.get(time_col or "", "") if time_col else "")

        order_id = (raw.get(order_col) or "").strip() if order_col else ""
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
                order_id,
            ]
        )
        external_id = (
            f"degiro-order-{order_id}" if order_id else f"degiro-csv-{tx_hash[:16]}"
        )

        rows.append(
            DegiroRow(
                external_id=external_id,
                symbol=symbol,
                name=name,
                transaction_type=transaction_type,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=fee,
                total_eur=total_eur,
                occurred_at=occurred_at,
                transaction_hash=tx_hash,
                mic=mic,
                description=description.strip(),
                currency=currency.upper() if currency else "EUR",
                line_number=index,
            )
        )

    return CsvParseResult(rows=rows, rows_in_file=data_row_count, skipped=skipped)


def _normalize_header(name: str) -> str:
    return normalize_header(name)


def _normalize_mic(value: str) -> str:
    raw = (value or "").strip().upper()
    if len(raw) == 4 and raw.isalpha():
        return raw
    return raw[:12]
