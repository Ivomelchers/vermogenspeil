"""Deterministische kolommapping zonder AI — schaalbaar per platform-schema."""

from __future__ import annotations

from difflib import SequenceMatcher

from apps.integrations.csv.column_schema import PlatformColumnSchema
from apps.integrations.csv.column_mapping_constants import is_forbidden_description_header
from apps.integrations.csv.headers import normalize_header
from apps.integrations.csv.mapping_sanity import (
    _settlement_header_in_file,
    is_weak_total_header,
)
from apps.integrations.csv.platform_mapping_hints import get_platform_mapping_hints


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def _token_overlap(a: str, b: str) -> float:
    ta = set(a.split())
    tb = set(b.split())
    if not ta or not tb:
        return 0.0
    return len(ta & tb) / max(len(ta), len(tb))


def _header_score(header: str, field_aliases: frozenset[str], label: str) -> float:
    norm = normalize_header(header)
    best = 0.0
    for alias in field_aliases:
        best = max(best, _similarity(norm, alias), _token_overlap(norm, alias))
    best = max(best, _similarity(norm, normalize_header(label)))
    return best


def _keyword_score(header: str, keywords: tuple[str, ...]) -> float:
    norm = normalize_header(header)
    hits = sum(1 for kw in keywords if kw in norm)
    if hits == 0:
        return 0.0
    return min(0.95, 0.65 + hits * 0.12)


def enrich_column_mapping(
    schema: PlatformColumnSchema,
    *,
    original_headers: list[str],
    mapped: dict[str, str],
    min_score: float = 0.78,
) -> dict[str, str]:
    """
    Vul ontbrekende velden aan via aliases, settlement-detectie en keyword-hints.
    Overschrijft bestaande mappings niet.
    """
    result = dict(mapped)
    used = set(result.values())
    available = [h for h in original_headers if h and h not in used]

    hints = get_platform_mapping_hints(schema.platform)
    keyword_map = dict(hints.header_keyword_hints) if hints else {}

    if "total" not in result:
        settlement = _settlement_header_in_file(original_headers)
        if settlement and settlement not in used:
            result["total"] = settlement
            used.add(settlement)
            available = [h for h in available if h != settlement]

    fields_by_canonical = {f.canonical: f for f in schema.fields}

    for field_def in schema.fields:
        if field_def.canonical in result:
            continue
        if field_def.canonical == "description":
            continue

        best_header: str | None = None
        best_score = 0.0

        for header in available:
            if field_def.canonical == "total" and is_weak_total_header(header):
                continue
            if field_def.canonical == "description" and is_forbidden_description_header(header):
                continue

            score = _header_score(header, field_def.aliases, field_def.label)
            kw = keyword_map.get(field_def.canonical)
            if kw:
                score = max(score, _keyword_score(header, kw))

            if score > best_score:
                best_score = score
                best_header = header

        if best_header and best_score >= min_score:
            result[field_def.canonical] = best_header
            used.add(best_header)
            available.remove(best_header)

    if "description" not in result:
        desc_field = fields_by_canonical.get("description")
        if desc_field:
            best_header = None
            best_score = 0.0
            for header in available:
                if is_forbidden_description_header(header):
                    continue
                score = max(
                    _header_score(header, desc_field.aliases, desc_field.label),
                    _keyword_score(header, keyword_map.get("description", ())),
                )
                if score > best_score:
                    best_score = score
                    best_header = header
            if best_header and best_score >= min_score:
                result["description"] = best_header

    return result
