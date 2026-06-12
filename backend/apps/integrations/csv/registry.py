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


def _load_bybit_entry() -> CsvParserEntry:
    from apps.integrations.bybit.fingerprint import bybit_fingerprint_score, bybit_missing_required
    from apps.integrations.bybit.import_service import import_bybit_csv_for_user
    from apps.integrations.bybit.parser import parse_bybit_csv

    return CsvParserEntry(
        platform=PlatformType.BYBIT,
        platform_display="Bybit",
        fingerprint_score=bybit_fingerprint_score,
        missing_required_headers=bybit_missing_required,
        parse=parse_bybit_csv,
        import_for_user=import_bybit_csv_for_user,
    )


def _load_okx_entry() -> CsvParserEntry:
    from apps.integrations.okx.fingerprint import okx_fingerprint_score, okx_missing_required
    from apps.integrations.okx.import_service import import_okx_csv_for_user
    from apps.integrations.okx.parser import parse_okx_csv

    return CsvParserEntry(
        platform=PlatformType.OKX,
        platform_display="OKX",
        fingerprint_score=okx_fingerprint_score,
        missing_required_headers=okx_missing_required,
        parse=parse_okx_csv,
        import_for_user=import_okx_csv_for_user,
    )


def _load_trading212_entry() -> CsvParserEntry:
    from apps.integrations.trading212.fingerprint import (
        trading212_fingerprint_score,
        trading212_missing_required,
    )
    from apps.integrations.trading212.import_service import import_trading212_csv_for_user
    from apps.integrations.trading212.parser import parse_trading212_csv

    return CsvParserEntry(
        platform=PlatformType.TRADING212,
        platform_display="Trading 212",
        fingerprint_score=trading212_fingerprint_score,
        missing_required_headers=trading212_missing_required,
        parse=parse_trading212_csv,
        import_for_user=import_trading212_csv_for_user,
    )


def _load_trade_republic_entry() -> CsvParserEntry:
    from apps.integrations.trade_republic.fingerprint import (
        trade_republic_fingerprint_score,
        trade_republic_missing_required,
    )
    from apps.integrations.trade_republic.import_service import import_trade_republic_csv_for_user
    from apps.integrations.trade_republic.parser import parse_trade_republic_csv

    return CsvParserEntry(
        platform=PlatformType.TRADE_REPUBLIC,
        platform_display="Trade Republic",
        fingerprint_score=trade_republic_fingerprint_score,
        missing_required_headers=trade_republic_missing_required,
        parse=parse_trade_republic_csv,
        import_for_user=import_trade_republic_csv_for_user,
    )


def _load_saxo_entry() -> CsvParserEntry:
    from apps.integrations.saxo.fingerprint import saxo_fingerprint_score, saxo_missing_required
    from apps.integrations.saxo.import_service import import_saxo_csv_for_user
    from apps.integrations.saxo.parser import parse_saxo_csv

    return CsvParserEntry(
        platform=PlatformType.SAXO,
        platform_display="Saxo Bank",
        fingerprint_score=saxo_fingerprint_score,
        missing_required_headers=saxo_missing_required,
        parse=parse_saxo_csv,
        import_for_user=import_saxo_csv_for_user,
    )


def _build_registry() -> dict[str, CsvParserEntry]:
    entries = [
        _load_degiro_entry(),
        _load_bybit_entry(),
        _load_okx_entry(),
        _load_trading212_entry(),
        _load_trade_republic_entry(),
        _load_saxo_entry(),
    ]
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
