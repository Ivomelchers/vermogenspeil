from apps.integrations.csv.base import CsvParseResult
from apps.integrations.csv.standard_import import import_standard_csv_for_user
from apps.integrations.models import PlatformType
from apps.integrations.trade_republic.parser import TradeRepublicParseError, parse_trade_republic_csv


def import_trade_republic_csv_for_user(
    user,
    file_content: str,
    *,
    label: str = "Trade Republic (CSV)",
    parse_result: CsvParseResult | None = None,
    source_filename: str = "",
    column_mapping: dict | None = None,
    ai_used: bool = False,
) -> dict:
    result = parse_result or parse_trade_republic_csv(file_content)
    return import_standard_csv_for_user(
        user,
        platform=PlatformType.TRADE_REPUBLIC,
        platform_display="Trade Republic",
        label=label,
        parse_result=result,
        source_filename=source_filename,
        column_mapping=column_mapping,
        ai_used=ai_used,
    )
