"""Bybit header-fingerprint."""

from apps.integrations.bybit.column_schema import BYBIT_SCHEMA
from apps.integrations.csv.column_schema import (
    fingerprint_score_from_schema,
    missing_required_labels,
)


def bybit_fingerprint_score(normalized_headers: set[str]) -> float:
    return fingerprint_score_from_schema(BYBIT_SCHEMA, normalized_headers)


def bybit_missing_required(normalized_headers: set[str]) -> list[str]:
    return missing_required_labels(BYBIT_SCHEMA, normalized_headers)
