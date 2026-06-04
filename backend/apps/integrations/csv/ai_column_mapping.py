"""Optionele AI-kolommapping (alleen headers + voorbeeldrijen, geen volledige import)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

import requests
from django.conf import settings

from apps.integrations.csv.column_schema import PlatformColumnSchema

logger = logging.getLogger(__name__)

CANONICAL_FIELDS = (
    "date",
    "time",
    "product",
    "isin",
    "description",
    "quantity",
    "price",
    "fee",
    "total",
    "currency",
    "local_value",
    "exchange_rate",
    "order_id",
)


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


def suggest_column_mapping_with_ai(
    schema: PlatformColumnSchema,
    *,
    file_headers: list[str],
    sample_rows: list[dict[str, str]],
) -> AiColumnMappingResult | None:
    """
    Vraag LLM om CSV-kolomkoppen te koppelen aan canonieke velden.
    Retourneert None als AI uit staat of de call faalt.
    """
    if not ai_column_mapping_enabled():
        return None

    api_key = settings.OPENAI_API_KEY
    model = getattr(settings, "CSV_AI_COLUMN_MODEL", "gpt-4o-mini")
    field_lines = "\n".join(
        f"- {f.canonical} ({f.label}): required={f.required}" for f in schema.fields
    )
    samples_json = json.dumps(sample_rows[:3], ensure_ascii=False)
    headers_json = json.dumps(file_headers, ensure_ascii=False)

    prompt = f"""Je koppelt broker CSV-kolomkoppen aan een vast schema voor platform "{schema.platform}".

Canonieke velden:
{field_lines}

CSV headers (exacte tekst):
{headers_json}

Eerste dataregels (JSON):
{samples_json}

Regels:
- Map alleen headers die echt in de lijst staan (exacte spelling).
- Laat canonieke velden weg als er geen passende header is.
- date en total zijn het belangrijkst; description is optioneel.
- Bij DEGIRO NL: map total naar "Totaal EUR" (afschrijfbedrag), NIET naar "Waarde EUR" (marktwaarde regel).
- Antwoord ALLEEN met JSON object: keys = canonical, values = exacte header string uit de CSV.

Voorbeeld: {{"date": "Datum", "total": "Totaal EUR"}}"""

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
                        "content": "Je bent een CSV-schema mapper voor fintech imports. Geen advies, alleen JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        body = response.json()
        content = body["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (requests.RequestException, KeyError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("AI column mapping failed: %s", exc)
        return None

    if not isinstance(parsed, dict):
        return None

    header_set = set(file_headers)
    mapped: dict[str, str] = {}
    for key, value in parsed.items():
        if key not in CANONICAL_FIELDS:
            continue
        if isinstance(value, str) and value in header_set:
            mapped[key] = value

    if not mapped:
        return None

    return AiColumnMappingResult(
        mapped_columns=mapped,
        confidence=0.85,
        reasoning="AI-kolommapping (headers alleen)",
        raw_response=content if isinstance(content, str) else "",
    )


def format_alias_maintenance_snippets(
    schema: PlatformColumnSchema,
    mapped_columns: dict[str, str],
    *,
    source: str,
) -> list[str]:
    """Tekst om handmatig in column_schema.py aliases toe te voegen (minder AI-kosten later)."""
    from apps.integrations.csv.headers import normalize_header

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
