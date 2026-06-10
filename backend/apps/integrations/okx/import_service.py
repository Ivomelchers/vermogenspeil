from apps.integrations.csv.base import CsvParseResult
from apps.integrations.csv.standard_import import import_standard_csv_for_user
from apps.integrations.models import PlatformType
from apps.integrations.okx.parser import parse_okx_csv


def import_okx_csv_for_user(
    user,
    file_content: str,
    *,
    label: str = "OKX (CSV)",
    parse_result: CsvParseResult | None = None,
    source_filename: str = "",
    column_mapping: dict | None = None,
    ai_used: bool = False,
) -> dict:
    result = parse_result or parse_okx_csv(
        file_content,
        column_mapping=column_mapping or None,
    )
    return import_standard_csv_for_user(
        user,
        platform=PlatformType.OKX,
        platform_display="OKX",
        label=label,
        parse_result=result,
        source_filename=source_filename,
        column_mapping=column_mapping,
        ai_used=ai_used,
        default_crypto=True,
    )
