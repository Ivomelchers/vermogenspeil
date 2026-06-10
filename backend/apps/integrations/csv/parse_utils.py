"""Gedeelde CSV-parse helpers voor broker- en exchange-imports."""

from __future__ import annotations

import csv
import hashlib
import io
import re
from datetime import datetime, timezone as dt_timezone
from decimal import Decimal, InvalidOperation

from django.utils import timezone

from apps.integrations.csv.base import CsvParseError
from apps.integrations.csv.headers import detect_delimiter, normalize_header


def parse_decimal(value: str) -> Decimal:
    cleaned = (value or "").strip().replace(",", ".")
    if not cleaned or cleaned in {"-", "—"}:
        return Decimal(0)
    cleaned = re.sub(r"[^\d.\-+]", "", cleaned)
    if not cleaned or cleaned in {".", "-", "+", "-.", "+."}:
        return Decimal(0)
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise CsvParseError(f"Ongeldig getal: {value}") from exc


def row_hash(parts: list[str]) -> str:
    return hashlib.sha256("|".join(parts).encode()).hexdigest()


def read_dict_rows(content: str) -> tuple[list[dict[str, str]], list[str], str]:
    """Return data rows, original headers, delimiter."""
    if not (content or "").strip():
        raise CsvParseError("CSV-bestand is leeg.")

    delimiter = detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        raise CsvParseError("CSV heeft geen kolomkoppen.")

    original_headers = [h for h in reader.fieldnames if h]
    rows: list[dict[str, str]] = []
    for raw in reader:
        if not any((v or "").strip() for v in raw.values()):
            continue
        rows.append({k: (v or "") for k, v in raw.items() if k is not None})

    if not rows:
        raise CsvParseError("CSV bevat geen dataregels.")

    return rows, original_headers, delimiter


def header_map(original_headers: list[str]) -> dict[str, str]:
    """normalized_header -> original header text."""
    mapping: dict[str, str] = {}
    for header in original_headers:
        mapping[normalize_header(header)] = header
    return mapping


def pick(row: dict[str, str], hmap: dict[str, str], *aliases: str) -> str:
    for alias in aliases:
        key = hmap.get(normalize_header(alias))
        if key and (row.get(key) or "").strip():
            return (row.get(key) or "").strip()
    return ""


def parse_datetime_flexible(value: str, time_value: str = "") -> datetime:
    text = (value or "").strip()
    if not text:
        raise CsvParseError("Ontbrekende datum/tijd in CSV-regel.")

    combined = f"{text} {time_value}".strip() if time_value else text
    patterns = (
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%d-%m-%Y %H:%M:%S",
        "%d-%m-%Y %H:%M",
        "%d-%m-%Y",
        "%d/%m/%Y %H:%M:%S",
        "%d/%m/%Y %H:%M",
        "%d/%m/%Y",
        "%d %b %y %H:%M %z",
        "%d %b %y %H:%M:%S %z",
        "%d %b %Y %H:%M %z",
        "%d %b %Y %H:%M:%S %z",
    )
    for fmt in patterns:
        try:
            parsed = datetime.strptime(combined, fmt)
            if parsed.tzinfo is None:
                return timezone.make_aware(parsed, timezone.get_current_timezone())
            return parsed.astimezone(timezone.get_current_timezone())
        except ValueError:
            continue

    normalized = combined.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
        if parsed.tzinfo is None:
            return timezone.make_aware(parsed, timezone.get_current_timezone())
        return parsed.astimezone(timezone.get_current_timezone())
    except ValueError as exc:
        raise CsvParseError(f"Ongeldige datum/tijd: {combined}") from exc


def parse_timestamp_ms(value: str) -> datetime:
    text = (value or "").strip()
    if not text:
        raise CsvParseError("Ontbrekende timestamp.")
    if text.isdigit():
        ms = int(text)
        if ms > 10_000_000_000:
            ms = ms // 1000
        return datetime.fromtimestamp(ms, tz=dt_timezone.utc).astimezone(timezone.get_current_timezone())
    return parse_datetime_flexible(text)


def eur_amount_from_parts(*values: str) -> Decimal:
    for value in values:
        amount = parse_decimal(value)
        if amount != 0:
            return abs(amount)
    return Decimal(0)
