"""Bybit spot trade CSV parser."""

from apps.integrations.bybit.column_schema import BYBIT_SCHEMA
from apps.integrations.bybit.fingerprint import bybit_fingerprint_score, bybit_missing_required
from apps.integrations.bybit.history import base_symbol_from_pair, map_bybit_side
from apps.integrations.csv.base import CsvParseError, CsvParseResult
from apps.integrations.csv.column_resolution import build_resolver_from_mapping
from apps.integrations.csv.column_schema import build_column_resolver
from apps.integrations.csv.parse_utils import (
    header_map,
    parse_decimal,
    parse_datetime_flexible,
    parse_timestamp_ms,
    read_dict_rows,
    row_hash,
)
from apps.integrations.csv.standard_import import StandardCsvRow
from apps.portfolio.models import AssetType


def _cell(row: dict[str, str], col: str | None) -> str:
    if not col:
        return ""
    return (row.get(col) or "").strip()


def _parse_executed_at(value: str):
    text = (value or "").strip()
    if text.isdigit():
        return parse_timestamp_ms(text)
    return parse_datetime_flexible(text)


def parse_bybit_csv(
    content: str,
    *,
    column_mapping: dict[str, str] | None = None,
) -> CsvParseResult:
    data_rows, original_headers, _ = read_dict_rows(content)
    hmap = header_map(original_headers)
    normalized = set(hmap.keys())

    if column_mapping:
        columns = build_resolver_from_mapping(BYBIT_SCHEMA, hmap, column_mapping)
        if not columns.get("symbol") or not columns.get("side"):
            raise CsvParseError(
                "Kolommapping mist verplichte velden (symbol of side). "
                "Controleer de export of meld nieuwe kolomnamen."
            )
    else:
        score = bybit_fingerprint_score(normalized)
        if score < 0.85:
            missing = bybit_missing_required(normalized)
            raise CsvParseError(
                "Dit is geen herkende Bybit spot trade-export. "
                f"Ontbrekende kolommen: {', '.join(missing) or 'onbekend format'}. "
                "Download het trade-overzicht uit uw Bybit-account."
            )
        columns = build_column_resolver(BYBIT_SCHEMA, hmap)

    symbol_col = columns.get("symbol")
    side_col = columns.get("side")
    qty_col = columns.get("quantity")
    price_col = columns.get("price")
    fee_col = columns.get("fee")
    order_col = columns.get("order_id")
    time_col = columns.get("executed_at")

    rows: list[StandardCsvRow] = []

    for index, raw in enumerate(data_rows, start=2):
        symbol_raw = _cell(raw, symbol_col)
        side_raw = _cell(raw, side_col)
        if not symbol_raw or not side_raw:
            continue

        try:
            quantity = abs(parse_decimal(_cell(raw, qty_col)))
            price = abs(parse_decimal(_cell(raw, price_col)))
            fee = abs(parse_decimal(_cell(raw, fee_col)))
            occurred_at = _parse_executed_at(_cell(raw, time_col))
        except CsvParseError as exc:
            raise CsvParseError(f"Regel {index}: {exc}") from exc

        if quantity <= 0:
            continue

        symbol = base_symbol_from_pair(symbol_raw)
        tx_type = map_bybit_side(side_raw)
        total = quantity * price
        order_id = _cell(raw, order_col)
        tx_hash = row_hash(
            [
                "bybit",
                symbol,
                tx_type,
                str(quantity),
                str(price),
                str(total),
                occurred_at.isoformat(),
                order_id,
            ]
        )
        external_id = f"bybit-order-{order_id}" if order_id else f"bybit-csv-{tx_hash[:16]}"

        rows.append(
            StandardCsvRow(
                external_id=external_id,
                symbol=symbol,
                name=symbol,
                transaction_type=tx_type,
                quantity=quantity,
                price_eur=price,
                fee_eur=fee,
                total_eur=total,
                occurred_at=occurred_at,
                transaction_hash=tx_hash,
                asset_type=AssetType.CRYPTO,
            )
        )

    return CsvParseResult(rows=rows, rows_in_file=len(data_rows))
