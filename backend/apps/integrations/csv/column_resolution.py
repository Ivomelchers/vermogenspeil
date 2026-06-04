"""Kolommapping: eerst vaste schema/aliases, dan fuzzy, dan optioneel AI."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field

from apps.integrations.csv.ai_column_mapping import (
    ai_column_mapping_enabled,
    format_alias_maintenance_snippets,
    suggest_column_mapping_with_ai,
)
from apps.integrations.csv.column_schema import (
    PlatformColumnSchema,
    analyze_column_schema,
    build_column_resolver,
    missing_required_labels,
)
from apps.integrations.csv.headers import detect_delimiter, normalize_header

FUZZY_AUTO_APPLY_THRESHOLD = 0.88


@dataclass
class ColumnMappingResolution:
    """Resultaat van kolom-koppeling vóór parse."""

    source: str
    mapped_columns: dict[str, str]
    missing_required: list[str]
    suggested_aliases: list[dict] = field(default_factory=list)
    maintenance_snippets: list[str] = field(default_factory=list)
    ai_used: bool = False

    @property
    def parser_ready(self) -> bool:
        return (
            not self.missing_required
            and bool(self.mapped_columns.get("date"))
            and bool(self.mapped_columns.get("total"))
        )


def _header_map_from_originals(original_headers: list[str]) -> dict[str, str]:
    return {normalize_header(name): name for name in original_headers if name}


def _resolver_to_mapped(resolver: dict[str, str | None]) -> dict[str, str]:
    return {k: v for k, v in resolver.items() if v}


def _merge_fuzzy_suggestions(
    schema: PlatformColumnSchema,
    mapped: dict[str, str],
    analysis,
) -> dict[str, str]:
    merged = dict(mapped)
    for item in analysis.suggested_aliases:
        if item.get("confidence", 0) < FUZZY_AUTO_APPLY_THRESHOLD:
            continue
        canonical = item.get("canonical")
        header = item.get("file_header")
        if canonical and header and canonical not in merged:
            merged[canonical] = header
    return merged


def _read_sample_rows(content: str, limit: int = 3) -> list[dict[str, str]]:
    delimiter = detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    rows: list[dict[str, str]] = []
    for raw in reader:
        if not any((v or "").strip() for v in raw.values()):
            continue
        rows.append({k: (v or "") for k, v in raw.items()})
        if len(rows) >= limit:
            break
    return rows


def resolve_column_mapping(
    schema: PlatformColumnSchema,
    *,
    original_headers: list[str],
    content: str = "",
    use_ai: bool = True,
) -> ColumnMappingResolution:
    """
    1. Vaste aliases (schema)
    2. Fuzzy suggesties automatisch toepassen bij hoge confidence
    3. Optioneel AI (alleen als 1+2 niet voldoende)
    """
    header_map = _header_map_from_originals(original_headers)
    normalized = set(header_map.keys())
    analysis = analyze_column_schema(
        schema,
        normalized_headers=normalized,
        original_headers=original_headers,
    )

    resolver = build_column_resolver(schema, header_map)
    mapped = _resolver_to_mapped(resolver)
    missing = missing_required_labels(schema, normalized)

    source = "schema"
    ai_used = False

    if missing:
        mapped = _merge_fuzzy_suggestions(schema, mapped, analysis)
        missing = _missing_for_mapped(schema, mapped)
        if missing and analysis.suggested_aliases:
            source = "fuzzy"

    if missing and use_ai and ai_column_mapping_enabled() and content.strip():
        ai_result = suggest_column_mapping_with_ai(
            schema,
            file_headers=original_headers,
            sample_rows=_read_sample_rows(content),
        )
        if ai_result:
            ai_used = True
            for canonical, header in ai_result.mapped_columns.items():
                if canonical not in mapped:
                    mapped[canonical] = header
            missing = _missing_for_mapped(schema, mapped)
            source = "ai" if not missing else f"{source}+ai"

    maintenance = format_alias_maintenance_snippets(
        schema,
        mapped,
        source="ai" if ai_used else source,
    )

    return ColumnMappingResolution(
        source=source,
        mapped_columns=mapped,
        missing_required=missing,
        suggested_aliases=analysis.suggested_aliases,
        maintenance_snippets=maintenance,
        ai_used=ai_used,
    )


def _missing_for_mapped(schema: PlatformColumnSchema, mapped: dict[str, str]) -> list[str]:
    missing: list[str] = []
    for field_def in schema.fields:
        if field_def.required and field_def.canonical not in mapped:
            missing.append(field_def.label)
    return missing


def build_resolver_from_mapping(
    schema: PlatformColumnSchema,
    header_map: dict[str, str],
    column_mapping: dict[str, str],
) -> dict[str, str | None]:
    """Resolver uit expliciete mapping (schema / fuzzy / AI)."""
    resolver: dict[str, str | None] = {}
    originals = set(header_map.values())
    for field_def in schema.fields:
        chosen = column_mapping.get(field_def.canonical)
        if chosen and chosen in originals:
            resolver[field_def.canonical] = chosen
        else:
            resolver[field_def.canonical] = build_column_resolver(schema, header_map).get(
                field_def.canonical
            )
    return resolver


def resolution_to_dict(resolution: ColumnMappingResolution) -> dict:
    return {
        "source": resolution.source,
        "mapped_columns": resolution.mapped_columns,
        "missing_required": resolution.missing_required,
        "suggested_aliases": resolution.suggested_aliases,
        "maintenance_snippets": resolution.maintenance_snippets,
        "ai_used": resolution.ai_used,
        "parser_ready": resolution.parser_ready,
        "ai_available": ai_column_mapping_enabled(),
    }
