"""Saxo Bank header-fingerprint (derived from column schema)."""

from apps.integrations.csv.column_schema import (
    fingerprint_score_from_schema,
    missing_required_labels,
)
from apps.integrations.saxo.column_schema import SAXO_SCHEMA


def saxo_fingerprint_score(normalized_headers: set[str]) -> float:
    """Score 0–1. Under 0.85: don't import as Saxo."""
    return fingerprint_score_from_schema(SAXO_SCHEMA, normalized_headers)


def saxo_missing_required(normalized_headers: set[str]) -> list[str]:
    return missing_required_labels(SAXO_SCHEMA, normalized_headers)
