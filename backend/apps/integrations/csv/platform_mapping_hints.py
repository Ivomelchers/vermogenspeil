"""Platform-specifieke hints voor kolommapping (AI + deterministische enrich)."""

from __future__ import annotations

from dataclasses import dataclass

from apps.integrations.models import PlatformType


@dataclass(frozen=True)
class PlatformMappingHints:
    """Uitbreidbare hints per broker — geen hardcoded DEGIRO in AI-module."""

    platform: str
    expected_delimiter: str | None = None
    ai_rules: tuple[str, ...] = ()
    # canonical → woorden die in een goede header mogen voorkomen (deterministisch)
    header_keyword_hints: tuple[tuple[str, tuple[str, ...]], ...] = ()


_GENERIC_AI_RULES: tuple[str, ...] = (
    "Gebruik ALLEEN header-strings uit ALLOWED_HEADERS — nooit verzinnen of hernoemen.",
    "Laat een canoniek veld weg als er geen duidelijke match is; gok niet.",
    "date en total zijn verplicht wanneer passende kolommen bestaan.",
    "Map total naar het afschrijf-/settlementbedrag, niet naar marktwaarde of lokaal bedrag "
    "als er een settlement-kolom is.",
    "Map currency naar valuta/CCY; map currency NOOIT naar description.",
    "Map description alleen bij duidelijke type/omschrijving-kolom — nooit venue, MIC, FX, ref.",
    "Map product, isin, quantity, price, fee, time, order_id wanneer een duidelijke "
    "header bestaat; optioneel maar sterk aanbevolen.",
)

_DEGIRO_AI_RULES: tuple[str, ...] = (
    "DEGIRO-export gebruikt puntkomma (;) als scheidingsteken.",
    'NL-export: total = "Totaal EUR" (afschrijfbedrag), NIET "Waarde EUR" (marktwaarde).',
    'Engelse drift: voorkeur "Settle total", "Net settlement", "Sum EUR" boven "Val EUR"/"Loc amt".',
    'order_id: "Order ID", "Order ref", "Ticket id", "Ref".',
)

_DEGIRO_KEYWORD_HINTS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("date", ("date", "datum", "day", "settlement date", "trade")),
    ("time", ("time", "hour", "clock", "execution")),
    ("product", ("product", "security", "instrument", "inst", "label", "name")),
    ("isin", ("isin", "identifier")),
    ("description", ("description", "omschrijving", "type", "soort", "action")),
    ("quantity", ("quantity", "qty", "shares", "units", "aantal", "stuks")),
    ("price", ("price", "px", "koers", "unit")),
    ("fee", ("fee", "cost", "kosten", "commission", "broker", "transaction cost")),
    ("total", ("total", "totaal", "settle", "settlement", "net", "sum", "bedrag")),
    ("currency", ("currency", "ccy", "munt", "pair", "fx ccy")),
    ("order_id", ("order", "ref", "ticket", "id")),
    ("mic", ("venue", "floor", "exchange", "mic", "market", "uitvoeringsplaats")),
    ("local_value", ("local", "loc amt", "amount local")),
    ("exchange_rate", ("exchange rate", "wisselkoers", "fx rate", "conversion")),
)


def get_platform_mapping_hints(platform: str) -> PlatformMappingHints | None:
    if platform == PlatformType.DEGIRO:
        return PlatformMappingHints(
            platform=platform,
            expected_delimiter=";",
            ai_rules=_GENERIC_AI_RULES + _DEGIRO_AI_RULES,
            header_keyword_hints=_DEGIRO_KEYWORD_HINTS,
        )
    return PlatformMappingHints(
        platform=platform,
        ai_rules=_GENERIC_AI_RULES,
    )


def build_ai_prompt_rules(platform: str) -> str:
    hints = get_platform_mapping_hints(platform)
    rules = hints.ai_rules if hints else _GENERIC_AI_RULES
    return "\n".join(f"- {rule}" for rule in rules)
