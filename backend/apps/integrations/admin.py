from django.contrib import admin

from apps.integrations.models import CsvImportDiagnostic, PlatformConnection, SyncJob


@admin.register(PlatformConnection)
class PlatformConnectionAdmin(admin.ModelAdmin):
    list_display = (
        "display_name",
        "user",
        "platform",
        "status",
        "is_demo",
        "last_synced_at",
        "is_active",
    )
    list_filter = ("platform", "status", "is_active", "is_demo")
    search_fields = ("user__email", "label")


@admin.register(SyncJob)
class SyncJobAdmin(admin.ModelAdmin):
    list_display = (
        "connection",
        "status",
        "positions_synced",
        "transactions_synced",
        "created_at",
    )
    list_filter = ("status",)


@admin.register(CsvImportDiagnostic)
class CsvImportDiagnosticAdmin(admin.ModelAdmin):
    list_display = (
        "platform",
        "event",
        "failure_reason",
        "rows_recognized",
        "created_at",
        "user",
    )
    list_filter = ("platform", "event", "failure_reason")
    readonly_fields = (
        "user",
        "platform",
        "schema_version",
        "event",
        "failure_reason",
        "file_headers",
        "missing_canonical",
        "unmapped_headers",
        "unknown_descriptions",
        "schema_warnings",
        "suggested_aliases",
        "rows_in_file",
        "rows_recognized",
        "created_at",
    )
    search_fields = ("user__email", "platform")
