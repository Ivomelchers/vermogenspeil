"""Optionele AI-kolommapping (alleen headers + voorbeeldrijen, geen volledige import)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import requests
from django.conf import settings

from apps.integrations.csv.column_mapping_constants import (
    CANONICAL_FIELDS,
    is_forbidden_description_header,
)
from apps.integrations.csv.column_schema import PlatformColumnSchema
from apps.integrations.csv.headers import normalize_header
from apps.integrations.csv.mapping_enrichment import enrich_column_mapping
from apps.integrations.csv.mapping_sanity import (
    sanitize_mapped_columns,
    validate_mapping_against_samples,
)
from apps.integrations.csv.platform_mapping_hints import build_ai_prompt_rules

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AiColumnMappingResult:
    mapped_columns: dict[str, str]
    confidence: float
    reasoning: str
    raw_response: str


def ai_column_mapping_enabled() -> bool:
    """AI aan zodra OPENAI_API_KEY gezet is, tenzij expliciet CSV_AI_COLUMN_MAPPING=false."""
    if not getattr(settings, "OPENAI_API_KEY", ""):
        return False
    return getattr(settings, "CSV_AI_COLUMN_MAPPING", True)


def _build_ai_prompt(
    schema: PlatformColumnSchema,
    *,
    file_headers: list[str],
    sample_rows: list[dict[str, str]],
) -> str:
    field_lines = "\n".join(
        f"- {f.canonical} ({f.label}): required={f.required}" for f in schema.fields
    )
    allowed_lines = "\n".join(f'- "{h}"' for h in file_headers)
    rules = build_ai_prompt_rules(schema.platform)
    samples_json = json.dumps(sample_rows[:3], ensure_ascii=False)

    return f"""PLATFORM: {schema.platform}

ALLOWED_HEADERS — values in your JSON MUST be copied exactly from this list (character-for-character):
{allowed_lines}

CANONICAL_FIELDS:
{field_lines}

SAMPLE_ROWS (for format validation only):
{samples_json}

RULES:
{rules}

OUTPUT FORMAT:
Return a single JSON object. Keys = canonical field names. Values = exact strings from ALLOWED_HEADERS.
Include date and total when matching headers exist. Omit any field you cannot map with high confidence.
Do not include keys outside CANONICAL_FIELDS. Do not include commentary or markdown."""


def _parse_ai_json(content: str, file_headers: list[str]) -> dict[str, str] | None:
    header_set = set(file_headers)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
        if not match:
            return None
        try:
            parsed = json.loads(match.group(0))
        except json.JSONDecodeError:
            return None

    if not isinstance(parsed, dict):
        return None

    mapped: dict[str, str] = {}
    for key, value in parsed.items():
        if key not in CANONICAL_FIELDS:
            continue
        if not isinstance(value, str):
            continue
        if value not in header_set:
            logger.warning("AI hallucinated header %r for %s — rejected", value, key)
            continue
        if key == "description" and is_forbidden_description_header(value):
            continue
        mapped[key] = value
    return mapped


def suggest_column_mapping_with_ai(
    schema: PlatformColumnSchema,
    *,
    file_headers: list[str],
    sample_rows: list[dict[str, str]],
    existing_mapped: dict[str, str] | None = None,
) -> AiColumnMappingResult | None:
    """
    Vraag LLM om CSV-kolomkoppen te koppelen aan canonieke velden.
    Retourneert None als AI uit staat of de call faalt.
    """
    if not ai_column_mapping_enabled():
        return None

    api_key = settings.OPENAI_API_KEY
    model = getattr(settings, "CSV_AI_COLUMN_MODEL", "gpt-4o-mini")
    prompt = _build_ai_prompt(schema, file_headers=file_headers, sample_rows=sample_rows)

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "temperature": 0,
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You map CSV column headers to canonical fintech import fields. "
                            "Output ONLY a JSON object. Never invent header names. "
                            "If uncertain, omit the field. Zero hallucination."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
    except (requests.RequestException, KeyError, TypeError) as exc:
        logger.warning("AI column mapping failed: %s", exc)
        return None

    mapped = _parse_ai_json(content if isinstance(content, str) else "", file_headers)
    if mapped is None:
        logger.warning("AI column mapping returned unparseable JSON")
        return None

    base = dict(existing_mapped or {})
    for canonical, header in mapped.items():
        if canonical not in base:
            base[canonical] = header

    base = sanitize_mapped_columns(base, original_headers=file_headers)
    base = enrich_column_mapping(
        schema,
        original_headers=file_headers,
        mapped=base,
        min_score=0.76,
    )

    if sample_rows:
        sanity = validate_mapping_against_samples(
            base,
            sample_rows,
            original_headers=file_headers,
        )
        if not sanity.ok:
            logger.warning("AI column mapping failed sanity check: %s", sanity.errors)
            return None
        base = sanity.mapped_columns

    if not base.get("date") or not base.get("total"):
        return None

    return AiColumnMappingResult(
        mapped_columns=base,
        confidence=0.85,
        reasoning="AI-kolommapping (headers + sanity)",
        raw_response=content if isinstance(content, str) else "",
    )


def format_alias_maintenance_snippets(
    schema: PlatformColumnSchema,
    mapped_columns: dict[str, str],
    *,
    source: str,
) -> list[str]:
    """Tekst om handmatig in column_schema.py aliases toe te voegen (minder AI-kosten later)."""
    snippets: list[str] = []
    fields_by_canonical = {f.canonical: f for f in schema.fields}

    for canonical, header in sorted(mapped_columns.items()):
        field = fields_by_canonical.get(canonical)
        if not field:
            continue
        norm = normalize_header(header)
        if norm in field.aliases:
            continue
        safe = norm.replace('"', '\\"')
        snippets.append(
            f'# {source}: voeg alias toe aan {schema.platform} / {canonical}\n'
            f'"{safe}",  # was: {header!r}'
        )
    return snippets
