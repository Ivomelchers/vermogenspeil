"""Trade Republic header-fingerprint (afgeleid van kolomschema)."""

from apps.integrations.csv.column_schema import (
    fingerprint_score_from_schema,
    missing_required_labels,
)
from apps.integrations.trade_republic.column_schema import TRADE_REPUBLIC_SCHEMA


def trade_republic_fingerprint_score(normalized_headers: set[str]) -> float:
    return fingerprint_score_from_schema(TRADE_REPUBLIC_SCHEMA, normalized_headers)


def trade_republic_missing_required(normalized_headers: set[str]) -> list[str]:
    return missing_required_labels(TRADE_REPUBLIC_SCHEMA, normalized_headers)
