"""Platform-detectie op basis van CSV-kolomkoppen."""

from dataclasses import dataclass

from apps.integrations.csv.base import CsvParseError
from apps.integrations.csv.headers import read_csv_headers
from apps.integrations.csv.registry import get_all_csv_parsers

# Minimale score om import zonder expliciete override toe te staan.
MIN_AUTO_DETECT_SCORE = 0.85
MIN_EXPECTED_PLATFORM_SCORE = 0.85
MIN_REPORT_MATCH_SCORE = 0.5


@dataclass(frozen=True)
class CsvDetectionMatch:
    platform: str
    platform_display: str
    confidence: float
    missing_headers: list[str]


def detect_csv_platform(content: str) -> list[CsvDetectionMatch]:
    """Rangschik platforms op header-match (hoogste eerst)."""
    try:
        normalized, _, _ = read_csv_headers(content)
    except ValueError as exc:
        raise CsvParseError(str(exc)) from exc

    matches: list[CsvDetectionMatch] = []
    for entry in get_all_csv_parsers():
        score = entry.fingerprint_score(normalized)
        if score < MIN_REPORT_MATCH_SCORE:
            continue
        matches.append(
            CsvDetectionMatch(
                platform=entry.platform,
                platform_display=entry.platform_display,
                confidence=round(score, 4),
                missing_headers=entry.missing_required_headers(normalized),
            )
        )

    matches.sort(key=lambda m: m.confidence, reverse=True)
    return matches


def validate_csv_for_platform(content: str, platform: str) -> CsvDetectionMatch:
    """Controleer of bestand bij gekozen platform hoort."""
    from apps.integrations.csv.registry import get_csv_parser

    entry = get_csv_parser(platform)
    try:
        normalized, _, _ = read_csv_headers(content)
    except ValueError as exc:
        raise CsvParseError(str(exc)) from exc

    score = entry.fingerprint_score(normalized)
    missing = entry.missing_required_headers(normalized)
    match = CsvDetectionMatch(
        platform=entry.platform,
        platform_display=entry.platform_display,
        confidence=round(score, 4),
        missing_headers=missing,
    )

    if score < MIN_EXPECTED_PLATFORM_SCORE:
        others = [
            m
            for m in detect_csv_platform(content)
            if m.platform != platform and m.confidence >= MIN_AUTO_DETECT_SCORE
        ]
        hint = ""
        if others:
            hint = (
                f" Dit bestand lijkt eerder op {others[0].platform_display} "
                f"({others[0].confidence:.0%})."
            )
        raise CsvParseError(
            f"Dit bestand past niet bij {entry.platform_display}. "
            f"Ontbrekende of onbekende kolommen: {', '.join(missing) or 'onbekend format'}.{hint} "
            "Download de officiële transactie-export van uw broker."
        )

    return match


def resolve_platform_for_import(
    content: str,
    *,
    platform: str | None = None,
) -> tuple[str, CsvDetectionMatch]:
    """Bepaal platform: expliciet + validatie, of auto-detect bij één duidelijke match."""
    if platform:
        match = validate_csv_for_platform(content, platform)
        return platform, match

    matches = detect_csv_platform(content)
    if not matches:
        raise CsvParseError(
            "We herkennen dit CSV-bestand niet. "
            "Gebruik de officiële transactie-export van een ondersteund platform."
        )

    best = matches[0]
    if best.confidence < MIN_AUTO_DETECT_SCORE:
        raise CsvParseError(
            "Het CSV-formaat is onduidelijk. Kies uw platform en upload opnieuw, "
            "of gebruik de officiële transactie-export."
        )

    if len(matches) > 1 and matches[1].confidence >= MIN_AUTO_DETECT_SCORE:
        names = ", ".join(f"{m.platform_display} ({m.confidence:.0%})" for m in matches[:3])
        raise CsvParseError(
            f"Meerdere platformen mogelijk: {names}. Geef expliciet aan welk platform dit is."
        )

    return best.platform, best
