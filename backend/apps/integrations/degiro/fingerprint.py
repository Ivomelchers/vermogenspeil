"""DEGIRO header-fingerprint (afgeleid van kolomschema)."""

from apps.integrations.csv.column_schema import (
    fingerprint_score_from_schema,
    missing_required_labels,
)
from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA


def degiro_fingerprint_score(normalized_headers: set[str]) -> float:
    """Score 0–1. Onder 0.85: niet als DEGIRO importeren."""
    return fingerprint_score_from_schema(DEGIRO_SCHEMA, normalized_headers)


def degiro_missing_required(normalized_headers: set[str]) -> list[str]:
    return missing_required_labels(DEGIRO_SCHEMA, normalized_headers)
