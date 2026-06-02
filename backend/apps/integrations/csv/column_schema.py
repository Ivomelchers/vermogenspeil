"""Platform-kolomschema's: aliases, mapping, drift-detectie (geen AI)."""

from dataclasses import dataclass, field
from difflib import SequenceMatcher


@dataclass(frozen=True)
class ColumnField:
    """Eén logisch veld in een broker-export."""

    canonical: str
    label: str
    aliases: frozenset[str]
    required: bool = False
    fingerprint: bool = True


@dataclass(frozen=True)
class PlatformColumnSchema:
    platform: str
    schema_version: str
    fields: tuple[ColumnField, ...]


@dataclass
class ColumnSchemaAnalysis:
    schema_version: str
    mapped_columns: dict[str, str]
    missing_required: list[str]
    unmapped_headers: list[str]
    schema_warnings: list[dict]
    suggested_aliases: list[dict]

    @property
    def has_blocking_issues(self) -> bool:
        return bool(self.missing_required)

    @property
    def has_warnings(self) -> bool:
        return bool(self.schema_warnings or self.suggested_aliases or self.unmapped_headers)


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _match_field(
    field_def: ColumnField,
    normalized_headers: set[str],
    header_map: dict[str, str],
) -> str | None:
    for alias in sorted(field_def.aliases, key=len, reverse=True):
        if alias in normalized_headers:
            return header_map[alias]
    return None


def build_column_resolver(
    schema: PlatformColumnSchema,
    header_map: dict[str, str],
) -> dict[str, str | None]:
    """canonical → originele CSV-kolomnaam (of None)."""
    normalized = set(header_map.keys())
    resolver: dict[str, str | None] = {}
    for field_def in schema.fields:
        resolver[field_def.canonical] = _match_field(field_def, normalized, header_map)
    return resolver


def fingerprint_score_from_schema(
    schema: PlatformColumnSchema,
    normalized_headers: set[str],
) -> float:
    fingerprint_fields = [f for f in schema.fields if f.fingerprint]
    if not fingerprint_fields:
        return 0.0

    matched = 0
    for field_def in fingerprint_fields:
        if normalized_headers & field_def.aliases:
            matched += 1
    return matched / len(fingerprint_fields)


def missing_required_labels(
    schema: PlatformColumnSchema,
    normalized_headers: set[str],
) -> list[str]:
    missing = []
    for field_def in schema.fields:
        if field_def.required and not (normalized_headers & field_def.aliases):
            missing.append(field_def.label)
    return missing


def analyze_column_schema(
    schema: PlatformColumnSchema,
    *,
    normalized_headers: set[str],
    original_headers: list[str],
) -> ColumnSchemaAnalysis:
    """
    Bepaal welke kolommen gemapt zijn, wat ontbreekt en wat mogelijk hernoemd is.
    Suggesties worden NIET automatisch toegepast.
    """
    header_map = {h: h for h in original_headers}
    # header_map from parser uses normalized->original; rebuild from originals
    from apps.integrations.csv.headers import normalize_header

    norm_to_original: dict[str, str] = {}
    for name in original_headers:
        norm_to_original[normalize_header(name)] = name

    mapped_columns: dict[str, str] = {}
    consumed_normalized: set[str] = set()

    missing_required: list[str] = []
    for field_def in schema.fields:
        hit = normalized_headers & field_def.aliases
        if hit:
            chosen = sorted(hit, key=len, reverse=True)[0]
            mapped_columns[field_def.canonical] = norm_to_original.get(chosen, chosen)
            consumed_normalized.add(chosen)
        elif field_def.required:
            missing_required.append(field_def.label)

    unmapped_normalized = normalized_headers - consumed_normalized
    unmapped_headers = [norm_to_original.get(n, n) for n in sorted(unmapped_normalized)]

    suggested_aliases: list[dict] = []
    schema_warnings: list[dict] = []

    for unmapped in unmapped_normalized:
        original = norm_to_original.get(unmapped, unmapped)
        best: tuple[float, ColumnField, str] | None = None
        for field_def in schema.fields:
            if field_def.canonical in mapped_columns:
                continue
            for alias in field_def.aliases:
                score = _similarity(unmapped, alias)
                if score >= 0.82 and (best is None or score > best[0]):
                    best = (score, field_def, alias)

        if best:
            score, field_def, alias = best
            suggested_aliases.append(
                {
                    "file_header": original,
                    "canonical": field_def.canonical,
                    "canonical_label": field_def.label,
                    "matched_alias": alias,
                    "confidence": round(score, 3),
                }
            )
            schema_warnings.append(
                {
                    "code": "suggested_column_alias",
                    "severity": "warning",
                    "message": (
                        f"Kolom '{original}' lijkt op '{field_def.label}' ({alias}). "
                        "Nog niet automatisch gekoppeld — meld dit als de import afwijkt."
                    ),
                    "file_header": original,
                    "canonical": field_def.canonical,
                }
            )

    _check_amount_column_drift(
        schema,
        mapped_columns,
        unmapped_normalized,
        norm_to_original,
        schema_warnings,
    )

    for unmapped in unmapped_headers:
        if any(s["file_header"] == unmapped for s in suggested_aliases):
            continue
        if len(unmapped) > 0:
            schema_warnings.append(
                {
                    "code": "unmapped_column",
                    "severity": "info",
                    "message": f"Kolom '{unmapped}' wordt niet gebruikt door de import.",
                    "file_header": unmapped,
                }
            )

    return ColumnSchemaAnalysis(
        schema_version=schema.schema_version,
        mapped_columns=mapped_columns,
        missing_required=missing_required,
        unmapped_headers=unmapped_headers,
        schema_warnings=_dedupe_warnings(schema_warnings),
        suggested_aliases=suggested_aliases,
    )


def _check_amount_column_drift(
    schema: PlatformColumnSchema,
    mapped_columns: dict[str, str],
    unmapped_normalized: set[str],
    norm_to_original: dict[str, str],
    schema_warnings: list[dict],
) -> None:
    total_field = next((f for f in schema.fields if f.canonical == "total"), None)
    if not total_field:
        return

    if "total" in mapped_columns:
        return

    amount_like = {"subtotal", "amount", "bedrag", "net amount", "gross amount"}
    for unmapped in unmapped_normalized:
        if unmapped in amount_like or any(k in unmapped for k in ("subtotal", "amount")):
            original = norm_to_original.get(unmapped, unmapped)
            schema_warnings.append(
                {
                    "code": "possible_amount_column_rename",
                    "severity": "warning",
                    "message": (
                        f"Kolom '{original}' lijkt een bedrag-kolom, maar '{total_field.label}' "
                        "ontbreekt. Totalen kunnen afwijken tot wij de mapping bijwerken."
                    ),
                    "file_header": original,
                    "canonical": "total",
                }
            )
            break


def _dedupe_warnings(warnings: list[dict]) -> list[dict]:
    seen: set[tuple[str, str]] = set()
    out: list[dict] = []
    for item in warnings:
        key = (item.get("code", ""), item.get("file_header", ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out


def schema_analysis_to_dict(analysis: ColumnSchemaAnalysis) -> dict:
    return {
        "schema_version": analysis.schema_version,
        "mapped_columns": analysis.mapped_columns,
        "missing_required": analysis.missing_required,
        "unmapped_headers": analysis.unmapped_headers,
        "schema_warnings": analysis.schema_warnings,
        "suggested_aliases": analysis.suggested_aliases,
        "has_blocking_issues": analysis.has_blocking_issues,
        "has_warnings": analysis.has_warnings,
    }
