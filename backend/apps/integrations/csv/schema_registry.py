"""Kolomschema per platform (uitbreidbaar)."""

from apps.integrations.csv.column_schema import PlatformColumnSchema
from apps.integrations.models import PlatformType


def get_column_schema(platform: str) -> PlatformColumnSchema | None:
    if platform == PlatformType.DEGIRO:
        from apps.integrations.degiro.column_schema import DEGIRO_SCHEMA

        return DEGIRO_SCHEMA
    return None
