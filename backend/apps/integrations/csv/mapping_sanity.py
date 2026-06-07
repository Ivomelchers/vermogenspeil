"""Sanity checks op kolommapping (AI, fuzzy, learned) vóór parse/import."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.integrations.csv.column_mapping_constants import (
    CANONICAL_FIELDS,
    CRITICAL_CANONICALS,
    is_forbidden_description_header,
)
from apps.integrations.csv.headers import normalize_header

# Kolommen die géén afschrijfbedrag/total mogen zijn (marktwaarde, lokaal, FX, …).
TOTAL_WEAK_HEADERS = frozenset(
    {
        "val eur",
        "value",
        "value in eur",
        "waarde eur",
        "waarde",
        "local val",
        "local value",
        "loc amt",
        "amount local",
        "eur value",
        "fx ccy",
        "subtotal",
        "sub total",
        "gross amount",
        "mutation",
    }
)

# Sterke total-kolomnamen (afschrijfbedrag incl. kosten).
SETTLEMENT_TOTAL_HEADERS = frozenset(
    {
        "total",
        "totaal",
        "totaal eur",
        "sum eur",
        "net sum",
        "settle total",
        "settlement amount",
        "net settlement",
        "net amount",
        "amount",
        "bedrag",
    }
)


@dataclass
class MappingSanityResult:
    ok: bool
    mapped_columns: dict[str, str]
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def _parse_decimal(value: str) -> Decimal | None:
    cleaned = (value or "").strip().replace(",", ".")
    if not cleaned or cleaned == "-":
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def _parse_date_value(date_value: str, time_value: str = "") -> datetime | None:
    date_part = (date_value or "").strip()
    if not date_part:
        return None
    time_part = (time_value or "00:00:00").strip()
    for fmt in ("%d-%m-%Y %H:%M:%S", "%d-%m-%Y %H:%M", "%d-%m-%Y", "%Y-%m-%d"):
        try:
            if fmt == "%d-%m-%Y" or fmt == "%Y-%m-%d":
                parsed = datetime.strptime(date_part, fmt)
            else:
                parsed = datetime.strptime(f"{date_part} {time_part}", fmt)
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        except ValueError:
            continue
    return None


def _settlement_header_in_file(original_headers: list[str]) -> str | None:
    header_map = {normalize_header(h): h for h in original_headers if h}
    for norm in SETTLEMENT_TOTAL_HEADERS:
        if norm in header_map:
            return header_map[norm]
    for norm, original in header_map.items():
        if any(token in norm for token in ("settle", "settlement", "totaal", "sum eur", "net ")):
            return original
    return None


def is_weak_total_header(header: str) -> bool:
    norm = normalize_header(header)
    if norm in TOTAL_WEAK_HEADERS:
        return True
    if norm in SETTLEMENT_TOTAL_HEADERS:
        return False
    # "Val EUR" / marktwaarde-achtig
    if "val" in norm and "eur" in norm and "settle" not in norm:
        return True
    return False


def is_safe_to_learn_total(header: str, *, original_headers: list[str]) -> bool:
    if is_weak_total_header(header):
        settlement = _settlement_header_in_file(original_headers)
        return settlement is not None and header == settlement
    return True


def prefer_settlement_total_mapping(
    mapped_columns: dict[str, str],
    original_headers: list[str],
) -> dict[str, str]:
    """Corrigeer total naar afschrijfbedrag-kolom als AI zwakke kolom koos."""
    total_header = mapped_columns.get("total")
    if not total_header:
        return mapped_columns

    settlement = _settlement_header_in_file(original_headers)
    if not settlement:
        return mapped_columns

    if is_weak_total_header(total_header) and total_header != settlement:
        updated = dict(mapped_columns)
        updated["total"] = settlement
        return updated
    return mapped_columns


def sanitize_mapped_columns(
    mapped_columns: dict[str, str],
    *,
    original_headers: list[str],
) -> dict[str, str]:
    """Verwijder onveilige mappings en corrigeer total waar mogelijk."""
    header_set = set(original_headers)
    cleaned: dict[str, str] = {}

    for canonical, header in mapped_columns.items():
        if not isinstance(header, str) or header not in header_set:
            continue
        if canonical == "description" and is_forbidden_description_header(header):
            continue
        cleaned[canonical] = header

    cleaned = prefer_settlement_total_mapping(cleaned, original_headers)
    return cleaned


def validate_mapping_against_samples(
    mapped_columns: dict[str, str],
    sample_rows: list[dict[str, str]],
    *,
    original_headers: list[str],
) -> MappingSanityResult:
    """Controleer date/total tegen echte voorbeeldrijen."""
    mapped = sanitize_mapped_columns(mapped_columns, original_headers=original_headers)
    errors: list[str] = []
    warnings: list[str] = []

    if not mapped.get("date"):
        errors.append("date ontbreekt in mapping")
    if not mapped.get("total"):
        errors.append("total ontbreekt in mapping")

    date_header = mapped.get("date")
    time_header = mapped.get("time")
    total_header = mapped.get("total")

    if total_header and is_weak_total_header(total_header):
        settlement = _settlement_header_in_file(original_headers)
        if settlement and total_header != settlement:
            errors.append(
                f"total mag niet '{total_header}' zijn als '{settlement}' het afschrijfbedrag is"
            )
        elif not settlement:
            warnings.append(f"total kolom '{total_header}' lijkt marktwaarde, niet afschrijfbedrag")

    if date_header and sample_rows:
        parsed_dates = 0
        for row in sample_rows[:3]:
            if _parse_date_value(row.get(date_header, ""), row.get(time_header or "", "")):
                parsed_dates += 1
        if parsed_dates == 0:
            errors.append(f"date kolom '{date_header}' parseert niet in voorbeeldrijen")

    if total_header and sample_rows:
        parsed_totals = 0
        for row in sample_rows[:3]:
            if _parse_decimal(row.get(total_header, "")) is not None:
                parsed_totals += 1
        if parsed_totals == 0:
            errors.append(f"total kolom '{total_header}' bevat geen parseerbare bedragen")

    quantity_header = mapped.get("quantity")
    if quantity_header and sample_rows:
        parsed_qty = 0
        for row in sample_rows[:3]:
            if _parse_decimal(row.get(quantity_header, "")) is not None:
                parsed_qty += 1
        if parsed_qty == 0:
            warnings.append(f"quantity kolom '{quantity_header}' parseert niet")

    ok = not errors and bool(mapped.get("date")) and bool(mapped.get("total"))
    return MappingSanityResult(ok=ok, mapped_columns=mapped, errors=errors, warnings=warnings)
