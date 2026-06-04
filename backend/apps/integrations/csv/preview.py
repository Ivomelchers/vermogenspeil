"""Dry-run CSV-preview: genormaliseerde transacties + duplicate-check, geen DB-write."""

from decimal import Decimal

from apps.integrations.csv.base import CsvParseError
from apps.integrations.csv.detection import detect_csv_platform, resolve_platform_for_import
from apps.integrations.csv.headers import read_csv_headers
from apps.integrations.csv.column_schema import analyze_column_schema, schema_analysis_to_dict
from apps.integrations.csv.diagnostics import record_csv_diagnostic
from apps.integrations.csv.parse_pipeline import column_mapping_payload, parse_csv_with_resolution
from apps.integrations.csv.registry import get_csv_parser, list_csv_platforms
from apps.integrations.csv.schema_registry import get_column_schema
from apps.integrations.models import CsvImportEvent
from apps.portfolio.models import Transaction
from apps.portfolio.services import get_or_create_default_portfolio

PREVIEW_TRANSACTION_LIMIT = 200
ISSUE_LIMIT = 50

FAILURE_UNSUPPORTED = "unsupported_platform"
FAILURE_MISMATCH = "platform_mismatch"
FAILURE_NO_ROWS = "no_recognized_rows"
FAILURE_PARSE = "parse_error"


def _decimal_str(value: Decimal | None) -> str | None:
    if value is None:
        return None
    return format(value.quantize(Decimal("0.01")), "f")


def _row_to_preview(row, *, status: str) -> dict:
    return {
        "date": row.occurred_at.date().isoformat(),
        "time": row.occurred_at.strftime("%H:%M:%S"),
        "transaction_type": row.transaction_type,
        "symbol": row.symbol,
        "name": row.name,
        "quantity": _decimal_str(row.quantity),
        "price_eur": _decimal_str(row.price_eur),
        "fee_eur": _decimal_str(row.fee_eur),
        "total_eur": _decimal_str(row.total_eur),
        "status": status,
        "transaction_hash": row.transaction_hash,
    }


def _rejection(
    *,
    failure_reason: str,
    message: str,
    file_headers: list[str],
    requested_platform: str | None = None,
    matches: list | None = None,
) -> dict:
    return {
        "status": "rejected",
        "failure_reason": failure_reason,
        "message": message,
        "file_headers": file_headers,
        "requested_platform": requested_platform,
        "supported_platforms": list_csv_platforms(),
        "matches": matches or [],
        "summary": None,
        "transactions": [],
        "issues": [],
        "can_confirm_import": False,
        "column_schema": None,
        "has_schema_warnings": False,
        "column_mapping": column_mapping_payload(None),
    }


def _analyze_schema(platform: str, normalized: set[str], original_headers: list[str]):
    schema = get_column_schema(platform)
    if not schema:
        return None
    return analyze_column_schema(
        schema,
        normalized_headers=normalized,
        original_headers=original_headers,
    )


def preview_csv_for_user(
    user,
    content: str,
    *,
    platform: str | None = None,
) -> dict:
    """
    Parse en classify zonder import.
    Bij verkeerd/ongekend platform: status=rejected + failure_reason (geen stille fout).
    """
    try:
        normalized, _, original_headers = read_csv_headers(content)
        file_headers = sorted(original_headers)[:40]
    except ValueError as exc:
        return _rejection(
            failure_reason=FAILURE_PARSE,
            message=str(exc),
            file_headers=[],
            requested_platform=platform,
        )

    matches_raw = detect_csv_platform(content)
    matches = [
        {
            "platform": m.platform,
            "platform_display": m.platform_display,
            "confidence": m.confidence,
            "missing_headers": m.missing_headers,
        }
        for m in matches_raw
    ]

    try:
        resolved_platform, detection = resolve_platform_for_import(content, platform=platform)
    except CsvParseError as exc:
        if platform:
            reason = FAILURE_MISMATCH
            msg = str(exc)
        elif not matches:
            reason = FAILURE_UNSUPPORTED
            msg = (
                "Dit CSV-bestand hoort niet bij een platform dat wij ondersteunen. "
                f"Gevonden kolommen: {', '.join(file_headers[:12])}"
                f"{'…' if len(file_headers) > 12 else ''}. "
                "Kies het juiste platform bij upload of gebruik de officiële export van "
                "DEGIRO (Transactions)."
            )
        else:
            reason = FAILURE_UNSUPPORTED
            msg = str(exc)

        rejection = _rejection(
            failure_reason=reason,
            message=msg,
            file_headers=file_headers,
            requested_platform=platform,
            matches=matches,
        )
        record_csv_diagnostic(
            user,
            platform=platform or (matches[0]["platform"] if matches else "unknown"),
            event=CsvImportEvent.REJECTED,
            failure_reason=reason,
            file_headers=file_headers,
        )
        return rejection

    entry = get_csv_parser(resolved_platform)
    schema_analysis = _analyze_schema(resolved_platform, normalized, original_headers)

    try:
        parse_result, mapping_resolution = parse_csv_with_resolution(
            entry,
            content,
            original_headers=original_headers,
        )
    except CsvParseError as exc:
        return _rejection(
            failure_reason=FAILURE_PARSE,
            message=str(exc),
            file_headers=file_headers,
            requested_platform=platform or resolved_platform,
            matches=matches,
        )

    portfolio = get_or_create_default_portfolio(user)
    existing_hashes = set(
        Transaction.objects.filter(portfolio=portfolio).values_list(
            "transaction_hash",
            flat=True,
        )
    )

    transactions: list[dict] = []
    new_count = 0
    duplicate_count = 0

    for row in parse_result.rows[:PREVIEW_TRANSACTION_LIMIT]:
        is_duplicate = row.transaction_hash in existing_hashes
        if is_duplicate:
            duplicate_count += 1
            status = "duplicate"
        else:
            new_count += 1
            status = "new"
        transactions.append(_row_to_preview(row, status=status))

    truncated = len(parse_result.rows) > PREVIEW_TRANSACTION_LIMIT

    issues = [
        {
            "line_number": s.line_number,
            "reason": s.reason,
            "description": s.description,
            "preview": s.preview,
            "suggestion": _issue_suggestion(s.reason),
        }
        for s in parse_result.skipped[:ISSUE_LIMIT]
    ]

    skipped_unrecognized = sum(1 for s in parse_result.skipped if s.reason == "unknown_description")
    skipped_other = sum(
        1
        for s in parse_result.skipped
        if s.reason not in ("unknown_description", "duplicate")
    )

    has_gaps = bool(skipped_unrecognized or skipped_other)
    schema_payload = schema_analysis_to_dict(schema_analysis) if schema_analysis else None
    has_schema_warnings = bool(schema_payload and schema_payload.get("has_warnings"))
    can_confirm = new_count > 0 and not (
        schema_analysis and schema_analysis.has_blocking_issues
    )

    record_csv_diagnostic(
        user,
        platform=resolved_platform,
        event=CsvImportEvent.PREVIEW,
        file_headers=file_headers,
        schema_analysis=schema_analysis,
        unknown_descriptions=parse_result.unknown_descriptions[:20],
        rows_in_file=parse_result.rows_in_file,
        rows_recognized=parse_result.rows_recognized,
    )

    return {
        "status": "ok",
        "failure_reason": None,
        "message": None,
        "platform": resolved_platform,
        "platform_display": entry.platform_display,
        "file_headers": file_headers,
        "detection": {
            "confidence": detection.confidence,
            "missing_headers": detection.missing_headers,
        },
        "matches": matches,
        "summary": {
            "rows_in_file": parse_result.rows_in_file,
            "rows_recognized": parse_result.rows_recognized,
            "new": new_count,
            "duplicate": duplicate_count,
            "skipped_unrecognized": skipped_unrecognized,
            "skipped_other": skipped_other,
            "transactions_truncated": truncated,
            "transactions_total": len(parse_result.rows),
        },
        "transactions": transactions,
        "issues": issues,
        "unknown_descriptions": parse_result.unknown_descriptions[:20],
        "has_import_gaps": has_gaps,
        "can_confirm_import": can_confirm,
        "confirm_hint": (
            "Bevestig alleen als de nieuwe transacties kloppen met uw broker-export."
            if can_confirm
            else "Geen nieuwe transacties om te importeren."
        ),
        "column_schema": schema_payload,
        "has_schema_warnings": has_schema_warnings,
        "column_mapping": column_mapping_payload(mapping_resolution),
    }


def _issue_suggestion(reason: str) -> str:
    if reason == "unknown_description":
        return "Voeg handmatig toe via Transacties, of meld deze omschrijving zodat wij de import kunnen uitbreiden."
    if reason == "zero_amount":
        return "Controleer de regel in uw export; mogelijk lege of administratieve regel."
    return "Controleer de regel in uw broker-export."
