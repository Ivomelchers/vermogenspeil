"""OKX header-fingerprint."""

from apps.integrations.csv.column_schema import (
    fingerprint_score_from_schema,
    missing_required_labels,
)
from apps.integrations.okx.column_schema import OKX_SCHEMA


def okx_fingerprint_score(normalized_headers: set[str]) -> float:
    return fingerprint_score_from_schema(OKX_SCHEMA, normalized_headers)


def okx_missing_required(normalized_headers: set[str]) -> list[str]:
    return missing_required_labels(OKX_SCHEMA, normalized_headers)
