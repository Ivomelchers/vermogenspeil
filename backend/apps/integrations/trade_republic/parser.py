"""Parse Trade Republic transactie-export naar StandardCsvRow."""

from __future__ import annotations

from apps.integrations.csv.base import CsvParseError, CsvParseResult, CsvSkippedRow
from apps.integrations.csv.column_schema import build_column_resolver
from apps.integrations.csv.parse_utils import (
    header_map,
    parse_datetime_flexible,
    parse_decimal,
    read_dict_rows,
    row_hash,
)
from apps.integrations.csv.standard_import import StandardCsvRow
from apps.integrations.trade_republic.classification import (
    amounts_for_row,
    classify_trade_republic_type,
    resolve_symbol,
)
from apps.integrations.trade_republic.column_schema import TRADE_REPUBLIC_SCHEMA
from apps.integrations.trade_republic.fingerprint import (
    trade_republic_fingerprint_score,
    trade_republic_missing_required,
)

TradeRepublicParseError = CsvParseError


def _row_preview(raw: dict[str, str], max_len: int = 120) -> str:
    parts = [str(v) for v in raw.values() if v]
    text = ";".join(parts)
    return text[:max_len] + ("…" if len(text) > max_len else "")


def _cell(row: dict[str, str], columns: dict[str, str | None], key: str) -> str:
    col = columns.get(key)
    return (row.get(col or "", "") if col else "").strip()


def parse_trade_republic_csv(content: str) -> CsvParseResult:
    """Parse Trade Republic transactie-export (komma of puntkomma)."""
    data_rows, original_headers, _delimiter = read_dict_rows(content)
    hmap = header_map(original_headers)
    normalized_headers = set(hmap.keys())

    score = trade_republic_fingerprint_score(normalized_headers)
    if score < 0.85:
        missing = trade_republic_missing_required(normalized_headers)
        raise CsvParseError(
            "Dit is geen herkende Trade Republic-transactie-export. "
            f"Ontbrekende kolommen: {', '.join(missing) or 'onbekend format'}. "
            "Gebruik een officiële of gevalideerde Trade Republic CSV-export."
        )

    columns = build_column_resolver(TRADE_REPUBLIC_SCHEMA, hmap)
    if not columns.get("id") or not columns.get("timestamp") or not columns.get("type"):
        raise CsvParseError(
            "Trade Republic-export mist verplichte kolommen (ID, Timestamp of Type)."
        )

    rows: list[StandardCsvRow] = []
    skipped: list[CsvSkippedRow] = []

    for index, raw in enumerate(data_rows, start=2):
        tx_type_label = _cell(raw, columns, "type")
        status = _cell(raw, columns, "status").lower()
        if status and status not in {"executed", "completed", "settled"}:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="non_executed",
                    description=f"{tx_type_label} ({status})",
                    preview=_row_preview(raw),
                )
            )
            continue

        try:
            shares_raw = parse_decimal(_cell(raw, columns, "shares"))
            rate_raw = parse_decimal(_cell(raw, columns, "rate"))
            debit_raw = parse_decimal(_cell(raw, columns, "debit"))
            credit_raw = parse_decimal(_cell(raw, columns, "credit"))
            commission_raw = parse_decimal(_cell(raw, columns, "commission"))
        except CsvParseError as exc:
            raise CsvParseError(f"Regel {index}: {exc}") from exc

        transaction_type = classify_trade_republic_type(tx_type_label)
        if not transaction_type:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="unknown_description",
                    description=tx_type_label or "(leeg)",
                    preview=_row_preview(raw),
                )
            )
            continue

        amounts = amounts_for_row(
            transaction_type,
            shares_raw=shares_raw,
            rate_raw=rate_raw,
            debit_raw=debit_raw,
            credit_raw=credit_raw,
            commission_raw=commission_raw,
        )
        if not amounts:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="zero_amount",
                    description=tx_type_label,
                    preview=_row_preview(raw),
                )
            )
            continue

        quantity, price_eur, total_eur, fee_eur = amounts
        instrument = _cell(raw, columns, "instrument")
        name = _cell(raw, columns, "name")
        symbol = resolve_symbol(
            transaction_type=transaction_type,
            instrument=instrument,
            name=name,
            line_number=index,
        )
        display_name = name or symbol

        try:
            occurred_at = parse_datetime_flexible(_cell(raw, columns, "timestamp"))
        except CsvParseError as exc:
            raise CsvParseError(f"Regel {index}: {exc}") from exc

        row_id = _cell(raw, columns, "id")
        tx_hash = row_hash(
            [
                "trade_republic",
                row_id or symbol,
                transaction_type,
                str(quantity),
                str(price_eur or ""),
                str(total_eur),
                occurred_at.isoformat(),
                tx_type_label,
            ]
        )
        external_id = (
            f"trade-republic-{row_id}" if row_id else f"trade-republic-csv-{tx_hash[:16]}"
        )

        rows.append(
            StandardCsvRow(
                external_id=external_id,
                symbol=symbol,
                name=display_name,
                transaction_type=transaction_type,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=fee_eur,
                total_eur=total_eur,
                occurred_at=occurred_at,
                transaction_hash=tx_hash,
            )
        )

    return CsvParseResult(rows=rows, rows_in_file=len(data_rows), skipped=skipped)
