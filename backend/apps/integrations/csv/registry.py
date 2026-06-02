"""Register van CSV-parsers per platform — uitbreidbaar zonder core-wijzigingen."""

from dataclasses import dataclass
from typing import Callable

from apps.integrations.csv.base import CsvParseResult
from apps.integrations.models import PlatformType


@dataclass(frozen=True)
class CsvParserEntry:
    platform: str
    platform_display: str
    fingerprint_score: Callable[[set[str]], float]
    missing_required_headers: Callable[[set[str]], list[str]]
    parse: Callable[[str], CsvParseResult]
    import_for_user: Callable


def _load_degiro_entry() -> CsvParserEntry:
    from apps.integrations.degiro.fingerprint import degiro_fingerprint_score, degiro_missing_required
    from apps.integrations.degiro.import_service import import_degiro_csv_for_user
    from apps.integrations.degiro.parser import parse_degiro_csv

    return CsvParserEntry(
        platform=PlatformType.DEGIRO,
        platform_display="DEGIRO",
        fingerprint_score=degiro_fingerprint_score,
        missing_required_headers=degiro_missing_required,
        parse=parse_degiro_csv,
        import_for_user=import_degiro_csv_for_user,
    )


def _build_registry() -> dict[str, CsvParserEntry]:
    entries = [_load_degiro_entry()]
    return {entry.platform: entry for entry in entries}


_CSV_REGISTRY: dict[str, CsvParserEntry] | None = None


def _registry() -> dict[str, CsvParserEntry]:
    global _CSV_REGISTRY
    if _CSV_REGISTRY is None:
        _CSV_REGISTRY = _build_registry()
    return _CSV_REGISTRY


def get_csv_parser(platform: str) -> CsvParserEntry:
    entry = _registry().get(platform)
    if not entry:
        supported = ", ".join(e.platform_display for e in get_all_csv_parsers())
        raise ValueError(f"CSV-import voor '{platform}' wordt nog niet ondersteund. Beschikbaar: {supported}")
    return entry


def get_all_csv_parsers() -> list[CsvParserEntry]:
    return list(_registry().values())


def list_csv_platforms() -> list[dict[str, str]]:
    return [
        {"platform": e.platform, "display_name": e.platform_display}
        for e in get_all_csv_parsers()
    ]
