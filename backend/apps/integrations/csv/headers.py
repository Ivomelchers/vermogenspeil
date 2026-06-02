"""CSV-header extractie (gedeeld door detectie en parsers)."""

import csv
import io
import re


def normalize_header(name: str) -> str:
    return re.sub(r"\s+", " ", (name or "").strip().lower())


def detect_delimiter(content: str) -> str:
    sample = content[:2048]
    return ";" if sample.count(";") > sample.count(",") else ","


def read_csv_headers(content: str) -> tuple[set[str], str, list[str]]:
    """Genormaliseerde headers, delimiter en originele veldnamen."""
    if not content.strip():
        raise ValueError("CSV-bestand is leeg.")

    delimiter = detect_delimiter(content)
    reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
    if not reader.fieldnames:
        raise ValueError("CSV heeft geen kolomkoppen.")

    original = [name for name in reader.fieldnames if name]
    normalized = {normalize_header(name) for name in original}
    return normalized, delimiter, original
