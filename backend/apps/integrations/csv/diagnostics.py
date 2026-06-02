"""Persist CSV schema/drift signalen (privacy: alleen headers + omschrijvingen)."""

from apps.integrations.csv.column_schema import ColumnSchemaAnalysis, schema_analysis_to_dict
from apps.integrations.models import CsvImportDiagnostic, CsvImportEvent


def record_csv_diagnostic(
    user,
    *,
    platform: str,
    event: str,
    failure_reason: str = "",
    file_headers: list[str] | None = None,
    schema_analysis: ColumnSchemaAnalysis | None = None,
    unknown_descriptions: list[str] | None = None,
    rows_in_file: int = 0,
    rows_recognized: int = 0,
) -> CsvImportDiagnostic:
    missing = []
    unmapped = []
    warnings = []
    suggestions = []
    schema_version = ""

    if schema_analysis:
        payload = schema_analysis_to_dict(schema_analysis)
        missing = payload["missing_required"]
        unmapped = payload["unmapped_headers"]
        warnings = payload["schema_warnings"]
        suggestions = payload["suggested_aliases"]
        schema_version = payload["schema_version"]

    return CsvImportDiagnostic.objects.create(
        user=user,
        platform=platform,
        schema_version=schema_version,
        event=event,
        failure_reason=failure_reason or "",
        file_headers=file_headers or [],
        missing_canonical=missing,
        unmapped_headers=unmapped,
        unknown_descriptions=unknown_descriptions or [],
        schema_warnings=warnings,
        suggested_aliases=suggestions,
        rows_in_file=rows_in_file,
        rows_recognized=rows_recognized,
    )
