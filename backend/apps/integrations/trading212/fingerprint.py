"""Trading 212 header-fingerprint (afgeleid van kolomschema)."""

from apps.integrations.csv.column_schema import (
    fingerprint_score_from_schema,
    missing_required_labels,
)
from apps.integrations.csv.detection import MIN_REPORT_MATCH_SCORE
from apps.integrations.trading212.column_schema import TRADING212_SCHEMA

_T212_DISTINCTIVE = frozenset(
    {
        "action",
        "no. of shares",
        "no of shares",
        "number of shares",
        "price / share",
        "price/share",
        "isin",
    }
)


def trading212_fingerprint_score(normalized_headers: set[str]) -> float:
    score = fingerprint_score_from_schema(TRADING212_SCHEMA, normalized_headers)
    if score < MIN_REPORT_MATCH_SCORE:
        return score
    if normalized_headers & _T212_DISTINCTIVE:
        return score
    # Generieke headers (bv. Coinbase: Timestamp + Transaction Type + Total) zijn geen T212.
    return min(score, MIN_REPORT_MATCH_SCORE - 0.01)

def trading212_missing_required(normalized_headers: set[str]) -> list[str]:
    return missing_required_labels(TRADING212_SCHEMA, normalized_headers)
