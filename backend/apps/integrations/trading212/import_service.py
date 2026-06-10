from apps.integrations.csv.base import CsvParseResult
from apps.integrations.csv.standard_import import import_standard_csv_for_user
from apps.integrations.models import PlatformType
from apps.integrations.trading212.parser import Trading212ParseError, parse_trading212_csv


def import_trading212_csv_for_user(
    user,
    file_content: str,
    *,
    label: str = "Trading 212 (CSV)",
    parse_result: CsvParseResult | None = None,
    source_filename: str = "",
    column_mapping: dict | None = None,
    ai_used: bool = False,
) -> dict:
    result = parse_result or parse_trading212_csv(file_content)
    return import_standard_csv_for_user(
        user,
        platform=PlatformType.TRADING212,
        platform_display="Trading 212",
        label=label,
        parse_result=result,
        source_filename=source_filename,
        column_mapping=column_mapping,
        ai_used=ai_used,
    )
