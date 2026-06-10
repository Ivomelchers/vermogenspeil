"""Parse Trading 212 activity-export naar StandardCsvRow."""

from __future__ import annotations

from decimal import Decimal

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
from apps.integrations.trading212.classification import (
    amounts_for_row,
    classify_trading212_action,
    resolve_symbol,
)
from apps.integrations.trading212.column_schema import TRADING212_SCHEMA
from apps.integrations.trading212.fingerprint import (
    trading212_fingerprint_score,
    trading212_missing_required,
)

Trading212ParseError = CsvParseError


def _row_preview(raw: dict[str, str], max_len: int = 120) -> str:
    parts = [str(v) for v in raw.values() if v]
    text = ";".join(parts)
    return text[:max_len] + ("…" if len(text) > max_len else "")


def _cell(row: dict[str, str], columns: dict[str, str | None], key: str) -> str:
    col = columns.get(key)
    return (row.get(col or "", "") if col else "").strip()


def parse_trading212_csv(content: str) -> CsvParseResult:
    """Parse Trading 212 activity-export (komma of puntkomma)."""
    data_rows, original_headers, _delimiter = read_dict_rows(content)
    hmap = header_map(original_headers)
    normalized_headers = set(hmap.keys())

    score = trading212_fingerprint_score(normalized_headers)
    if score < 0.85:
        missing = trading212_missing_required(normalized_headers)
        raise CsvParseError(
            "Dit is geen herkende Trading 212-activiteitexport. "
            f"Ontbrekende kolommen: {', '.join(missing) or 'onbekend format'}. "
            "Download het activiteitenoverzicht uit uw Trading 212-account."
        )

    columns = build_column_resolver(TRADING212_SCHEMA, hmap)
    if not columns.get("action") or not columns.get("time") or not columns.get("total"):
        raise CsvParseError(
            "Trading 212-export mist verplichte kolommen (Action, Time of Total)."
        )

    rows: list[StandardCsvRow] = []
    skipped: list[CsvSkippedRow] = []

    for index, raw in enumerate(data_rows, start=2):
        action = _cell(raw, columns, "action")
        try:
            quantity_raw = parse_decimal(_cell(raw, columns, "quantity"))
            price_raw = parse_decimal(_cell(raw, columns, "price"))
            total_raw = parse_decimal(_cell(raw, columns, "total"))
        except CsvParseError as exc:
            raise CsvParseError(f"Regel {index}: {exc}") from exc

        transaction_type = classify_trading212_action(action)
        if not transaction_type:
            if action:
                skipped.append(
                    CsvSkippedRow(
                        line_number=index,
                        reason="unknown_description",
                        description=action,
                        preview=_row_preview(raw),
                    )
                )
            else:
                skipped.append(
                    CsvSkippedRow(
                        line_number=index,
                        reason="unknown_description",
                        description="(leeg)",
                        preview=_row_preview(raw),
                    )
                )
            continue

        amounts = amounts_for_row(
            transaction_type,
            quantity_raw=quantity_raw,
            price_raw=price_raw,
            total_raw=total_raw,
        )
        if not amounts:
            skipped.append(
                CsvSkippedRow(
                    line_number=index,
                    reason="zero_amount",
                    description=action,
                    preview=_row_preview(raw),
                )
            )
            continue

        quantity, price_eur, total_eur = amounts
        isin = _cell(raw, columns, "isin")
        ticker = _cell(raw, columns, "ticker")
        name = _cell(raw, columns, "name")
        symbol = resolve_symbol(
            transaction_type=transaction_type,
            isin=isin,
            ticker=ticker,
            name=name,
            line_number=index,
        )
        display_name = name or ticker or symbol

        try:
            occurred_at = parse_datetime_flexible(_cell(raw, columns, "time"))
        except CsvParseError as exc:
            raise CsvParseError(f"Regel {index}: {exc}") from exc

        row_id = _cell(raw, columns, "id")
        tx_hash = row_hash(
            [
                "trading212",
                symbol,
                transaction_type,
                str(quantity),
                str(price_eur or ""),
                str(total_eur),
                occurred_at.isoformat(),
                action,
                row_id,
            ]
        )
        external_id = (
            f"trading212-{row_id}" if row_id else f"trading212-csv-{tx_hash[:16]}"
        )

        rows.append(
            StandardCsvRow(
                external_id=external_id,
                symbol=symbol,
                name=display_name,
                transaction_type=transaction_type,
                quantity=quantity,
                price_eur=price_eur,
                fee_eur=Decimal(0),
                total_eur=total_eur,
                occurred_at=occurred_at,
                transaction_hash=tx_hash,
            )
        )

    return CsvParseResult(rows=rows, rows_in_file=len(data_rows), skipped=skipped)
