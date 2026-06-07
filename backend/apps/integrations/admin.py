from django.contrib import admin

from apps.integrations.models import (
    CsvImportDiagnostic,
    PlatformConnection,
    PlatformImportBatch,
    SharedCsvColumnAlias,
    SharedCsvColumnAliasConfirmation,
    SyncJob,
    UserCsvColumnAlias,
)


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


@admin.register(PlatformImportBatch)
class PlatformImportBatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "connection",
        "platform",
        "source_filename",
        "transactions_imported",
        "created_at",
    )
    list_filter = ("platform", "connection_method")
    search_fields = ("user__email", "source_filename", "source_label")
    readonly_fields = ("created_at", "updated_at")


@admin.register(UserCsvColumnAlias)
class UserCsvColumnAliasAdmin(admin.ModelAdmin):
    list_display = ("user", "platform", "header_normalized", "canonical", "use_count", "updated_at")
    list_filter = ("platform", "canonical")
    search_fields = ("user__email", "header_normalized", "header_example")


@admin.register(SharedCsvColumnAlias)
class SharedCsvColumnAliasAdmin(admin.ModelAdmin):
    list_display = (
        "platform",
        "header_normalized",
        "canonical",
        "status",
        "confirmation_count",
        "conflict_count",
        "updated_at",
    )
    list_filter = ("platform", "status", "canonical")
    search_fields = ("header_normalized", "header_example")
    actions = ("mark_verified", "mark_disabled")

    @admin.action(description="Markeer als geverifieerd")
    def mark_verified(self, request, queryset):
        queryset.update(status="verified")

    @admin.action(description="Uitschakelen (vergiftiging stoppen)")
    def mark_disabled(self, request, queryset):
        queryset.update(status="disabled")


@admin.register(SharedCsvColumnAliasConfirmation)
class SharedCsvColumnAliasConfirmationAdmin(admin.ModelAdmin):
    list_display = ("alias", "user", "import_batch", "created_at")
    list_filter = ("alias__platform",)
