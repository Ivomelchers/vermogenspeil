"""Uniforme CSV-import met detectie, validatie en transparant importrapport."""

from apps.integrations.csv.base import CsvParseError
from apps.integrations.csv.column_schema import analyze_column_schema, schema_analysis_to_dict
from apps.integrations.csv.detection import resolve_platform_for_import
from apps.integrations.csv.diagnostics import record_csv_diagnostic
from apps.integrations.csv.headers import read_csv_headers
from apps.integrations.csv.parse_pipeline import column_mapping_payload, parse_csv_with_resolution
from apps.integrations.csv.registry import get_csv_parser
from apps.integrations.csv.schema_registry import get_column_schema
from apps.integrations.models import CsvImportEvent


def _trust_summary(
    *,
    rows_in_file: int,
    rows_recognized: int,
    imported: int,
    skipped_duplicate: int,
    skipped_unrecognized: int,
    skipped_other: int,
) -> str:
    parts = [f"{imported} transactie(s) nieuw geïmporteerd."]
    if skipped_duplicate:
        parts.append(f"{skipped_duplicate} dubbele regel(s) overgeslagen.")
    unrecognized = skipped_unrecognized + skipped_other
    if unrecognized:
        parts.append(
            f"{unrecognized} regel(s) niet geïmporteerd — controleer het importrapport "
            "en vergelijk met uw broker."
        )
    if rows_recognized < rows_in_file:
        parts.append(
            f"{rows_in_file - rows_recognized} van {rows_in_file} dataregel(s) niet als transactie herkend."
        )
    return " ".join(parts)


def import_csv_for_user(
    user,
    content: str,
    *,
    platform: str | None = None,
    label: str | None = None,
) -> dict:
    """
    Importeer CSV met platform-detectie of -validatie.
    Gooit CsvParseError bij leeg bestand, verkeerd platform of geen enkele herkende rij.
    """
    resolved_platform, detection = resolve_platform_for_import(content, platform=platform)
    entry = get_csv_parser(resolved_platform)

    try:
        _, _, original_headers = read_csv_headers(content)
    except ValueError as exc:
        raise CsvParseError(str(exc)) from exc

    parse_result, mapping_resolution = parse_csv_with_resolution(
        entry,
        content,
        original_headers=original_headers,
    )
    if parse_result.rows_recognized == 0:
        unknown = parse_result.unknown_descriptions[:8]
        hint = f" Onbekende omschrijvingen: {', '.join(unknown)}." if unknown else ""
        raise CsvParseError(
            f"Geen herkende transacties in {entry.platform_display}-CSV.{hint} "
            "Controleer of u de officiële transactie-export heeft geüpload."
        )

    default_label = f"{entry.platform_display} (CSV)"
    import_result = entry.import_for_user(
        user,
        content,
        label=label or default_label,
        parse_result=parse_result,
    )  # type: ignore[call-arg]

    skipped = parse_result.skipped
    skipped_unrecognized = sum(1 for s in skipped if s.reason == "unknown_description")
    skipped_other = sum(
        1 for s in skipped if s.reason not in ("unknown_description", "duplicate")
    )

    report = {
        "platform": resolved_platform,
        "platform_display": entry.platform_display,
        "detection": {
            "confidence": detection.confidence,
            "missing_headers": detection.missing_headers,
        },
        "rows_in_file": parse_result.rows_in_file,
        "rows_recognized": parse_result.rows_recognized,
        "rows_skipped_unrecognized": skipped_unrecognized,
        "rows_skipped_other": skipped_other,
        "skipped_rows": [
            {
                "line_number": s.line_number,
                "reason": s.reason,
                "description": s.description,
                "preview": s.preview,
            }
            for s in skipped[:50]
        ],
        "skipped_rows_truncated": len(skipped) > 50,
        "unknown_descriptions": parse_result.unknown_descriptions[:20],
        "trust_summary": _trust_summary(
            rows_in_file=parse_result.rows_in_file,
            rows_recognized=parse_result.rows_recognized,
            imported=import_result.get("transactions_imported", 0),
            skipped_duplicate=import_result.get("transactions_skipped", 0),
            skipped_unrecognized=skipped_unrecognized,
            skipped_other=skipped_other,
        ),
        "has_import_gaps": bool(skipped_unrecognized or skipped_other),
        "column_mapping": column_mapping_payload(mapping_resolution),
    }
    report.update(import_result)

    from apps.pricing.services.instrument_service import resolve_after_csv_import

    instrument_resolve = resolve_after_csv_import(parse_result)
    report["instrument_resolve"] = {
        "requested": instrument_resolve.requested,
        "resolved": instrument_resolve.resolved,
        "already_known": instrument_resolve.already_known,
        "failed": instrument_resolve.failed,
        "isins_failed": instrument_resolve.isins_failed[:10],
    }
    if instrument_resolve.failed:
        report["has_import_gaps"] = True

    schema_analysis = None
    schema = get_column_schema(resolved_platform)
    if schema:
        try:
            normalized, _, original = read_csv_headers(content)
            schema_analysis = analyze_column_schema(
                schema,
                normalized_headers=normalized,
                original_headers=original,
            )
            report["column_schema"] = schema_analysis_to_dict(schema_analysis)
            report["has_schema_warnings"] = schema_analysis.has_warnings
        except ValueError:
            pass

    try:
        _, _, original = read_csv_headers(content)
        file_headers_list = sorted(original)[:40]
    except ValueError:
        file_headers_list = []

    record_csv_diagnostic(
        user,
        platform=resolved_platform,
        event=CsvImportEvent.IMPORT,
        file_headers=file_headers_list,
        schema_analysis=schema_analysis,
        unknown_descriptions=parse_result.unknown_descriptions[:20],
        rows_in_file=parse_result.rows_in_file,
        rows_recognized=parse_result.rows_recognized,
    )

    return report
