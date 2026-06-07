"""AI-fallback voor onbekende DEGIRO Description-strings (alleen na vaste regels)."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from decimal import Decimal

import requests
from django.conf import settings

from apps.portfolio.models import TransactionType

logger = logging.getLogger(__name__)

ALLOWED_TYPES = frozenset(
    {
        TransactionType.BUY,
        TransactionType.SELL,
        TransactionType.DIVIDEND,
        TransactionType.DEPOSIT,
        TransactionType.WITHDRAWAL,
        TransactionType.FEE,
        TransactionType.OTHER,
    }
)


@dataclass(frozen=True)
class DescriptionRowContext:
    description: str
    quantity: Decimal
    total: Decimal
    fee: Decimal
    has_product: bool
    has_isin: bool


def ai_description_classification_enabled() -> bool:
    if not getattr(settings, "OPENAI_API_KEY", ""):
        return False
    return getattr(settings, "CSV_AI_DESCRIPTION_CLASSIFICATION", True)


def _sanitize_ai_type(raw: str | None) -> str | None:
    if not raw or not isinstance(raw, str):
        return None
    normalized = raw.strip().lower().replace(" ", "_")
    aliases = {
        "purchase": TransactionType.BUY,
        "sale": TransactionType.SELL,
        "withdraw": TransactionType.WITHDRAWAL,
        "costs": TransactionType.FEE,
        "cost": TransactionType.FEE,
        "tax": TransactionType.FEE,
        "interest": TransactionType.OTHER,
        "fx": TransactionType.OTHER,
        "transfer": TransactionType.OTHER,
    }
    if normalized in aliases:
        return aliases[normalized]
    if normalized in ALLOWED_TYPES:
        return normalized
    return None


def _passes_sanity(tx_type: str, ctx: DescriptionRowContext) -> bool:
    if tx_type in (TransactionType.BUY, TransactionType.SELL):
        return ctx.quantity != 0 or ctx.has_product or ctx.has_isin
    if tx_type in (TransactionType.DEPOSIT, TransactionType.WITHDRAWAL):
        return True
    if tx_type == TransactionType.DIVIDEND:
        return ctx.has_isin or ctx.has_product or ctx.total != 0
    if tx_type == TransactionType.FEE:
        return ctx.total != 0 or ctx.fee > 0
    if tx_type == TransactionType.OTHER:
        return ctx.total != 0
    return False


def classify_unknown_descriptions_with_ai(
    contexts: list[DescriptionRowContext],
) -> dict[str, str]:
    """
    Eén AI-call per unieke onbekende omschrijving (batch).
    Key = exacte description string, value = TransactionType.
    """
    if not ai_description_classification_enabled() or not contexts:
        return {}

    unique: dict[str, DescriptionRowContext] = {}
    for ctx in contexts:
        desc = (ctx.description or "").strip()
        if desc and desc not in unique:
            unique[desc] = ctx

    if not unique:
        return {}

    api_key = settings.OPENAI_API_KEY
    model = getattr(settings, "CSV_AI_COLUMN_MODEL", "gpt-4o-mini")

    payload_rows = [
        {
            "description": desc,
            "quantity": str(ctx.quantity),
            "total_eur": str(ctx.total),
            "fee_eur": str(ctx.fee),
            "has_product": ctx.has_product,
            "has_isin": ctx.has_isin,
        }
        for desc, ctx in unique.items()
    ]

    allowed = ", ".join(sorted(ALLOWED_TYPES))
    prompt = f"""Platform: DEGIRO broker CSV import.

Classify each row's Dutch/English transaction description into exactly ONE type.

ALLOWED_TYPES (only these values):
{allowed}

INPUT (unique descriptions with numeric context):
{json.dumps(payload_rows, ensure_ascii=False)}

RULES:
- Use ONLY allowed types. If unsure, use "other".
- "buy"/"sell" need shares changing (quantity != 0) or a product/ISIN.
- "deposit"/"withdrawal" = cash to/from account (often no ISIN).
- "dividend" = income on a holding (often quantity 0, positive total, has ISIN).
- "fee" = costs, taxes, broker charges (often quantity 0, negative total).
- "other" = FX, interest, corporate actions, unclear admin lines.
- Do NOT invent types. Do NOT explain.

OUTPUT: JSON object mapping each exact "description" string to one ALLOWED_TYPE.
Example: {{"Degiro Fee": "fee", "Valuta Creditering": "other"}}"""

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
                            "You classify broker CSV transaction descriptions. "
                            "Output ONLY JSON. Zero hallucination — only allowed types."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        parsed = json.loads(content)
    except (requests.RequestException, KeyError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("AI description classification failed: %s", exc)
        return {}

    if not isinstance(parsed, dict):
        return {}

    result: dict[str, str] = {}
    for desc, ctx in unique.items():
        raw_type = parsed.get(desc)
        if raw_type is None:
            for key, value in parsed.items():
                if isinstance(key, str) and key.strip().lower() == desc.lower():
                    raw_type = value
                    break
        tx_type = _sanitize_ai_type(raw_type if isinstance(raw_type, str) else None)
        if tx_type and _passes_sanity(tx_type, ctx):
            result[desc] = tx_type
        elif tx_type:
            logger.warning(
                "AI description type %s rejected by sanity for %r",
                tx_type,
                desc[:60],
            )
    return result
