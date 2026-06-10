"""Kolomschema per platform (uitbreidbaar)."""

from apps.integrations.csv.column_schema import PlatformColumnSchema
from apps.integrations.models import PlatformType


def get_column_schema(platform: str) -> PlatformColumnSchema | None:
    if platform == PlatformType.DEGIRO:
        from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA

        return DEGIRO_SCHEMA
    if platform == PlatformType.TRADING212:
        from apps.integrations.trading212.column_schema import TRADING212_SCHEMA

        return TRADING212_SCHEMA
    if platform == PlatformType.TRADE_REPUBLIC:
        from apps.integrations.trade_republic.column_schema import TRADE_REPUBLIC_SCHEMA

        return TRADE_REPUBLIC_SCHEMA
    return None
