"""Parse-pipeline: eerst vaste parser, bij falen kolommapping (fuzzy/AI) en opnieuw proberen."""

from __future__ import annotations

from apps.integrations.csv.base import CsvParseError, CsvParseResult
from apps.integrations.csv.column_resolution import (
    ColumnMappingResolution,
    resolution_to_dict,
    resolve_column_mapping,
)
from apps.integrations.csv.registry import CsvParserEntry
from apps.integrations.csv.schema_registry import get_column_schema
from apps.integrations.models import PlatformType


def parse_csv_with_resolution(
    entry: CsvParserEntry,
    content: str,
    *,
    original_headers: list[str],
    column_mapping_override: dict[str, str] | None = None,
    user=None,
) -> tuple[CsvParseResult, ColumnMappingResolution | None]:
    """
    1. Normale parser (schema/aliases) — geen AI
    2. Bij CsvParseError: resolve_column_mapping (fuzzy, optioneel AI) en retry

    column_mapping_override: mapping uit preview — voorkomt tweede AI-call bij import.
    """
    if column_mapping_override:
        schema = get_column_schema(entry.platform)
        if schema and entry.platform == PlatformType.DEGIRO:
            mapped = {
                k: v
                for k, v in column_mapping_override.items()
                if isinstance(k, str) and isinstance(v, str) and v.strip()
            }
            if mapped.get("date") and mapped.get("total"):
                from apps.integrations.degiro.parser import parse_degiro_csv

                result = parse_degiro_csv(content, column_mapping=mapped)
                resolution = ColumnMappingResolution(
                    source="preview",
                    mapped_columns=mapped,
                    missing_required=[],
                    ai_used=False,
                )
                return result, resolution

    try:
        return entry.parse(content), None
    except CsvParseError as first_exc:
        first_error = first_exc

    schema = get_column_schema(entry.platform)
    if not schema:
        raise first_error from first_exc

    resolution = resolve_column_mapping(
        schema,
        original_headers=original_headers,
        content=content,
        use_ai=True,
        user=user,
    )
    if not resolution.parser_ready:
        missing = resolution.missing_required
        extra = "date en total" if not missing else ", ".join(missing)
        raise CsvParseError(
            f"Kolommapping onvolledig ({extra}). "
            "Voeg de export toe als fixture of meld de kolomnamen via support."
        ) from first_error

    if entry.platform == PlatformType.DEGIRO:
        from apps.integrations.degiro.parser import parse_degiro_csv

        result = parse_degiro_csv(content, column_mapping=resolution.mapped_columns)
        return result, resolution

    raise first_error from first_exc


def column_mapping_payload(resolution: ColumnMappingResolution | None) -> dict:
    if resolution is None:
        return {
            "source": "schema",
            "mapped_columns": {},
            "missing_required": [],
            "suggested_aliases": [],
            "maintenance_snippets": [],
            "ai_used": False,
            "parser_ready": True,
            "ai_available": False,
        }
    return resolution_to_dict(resolution)
