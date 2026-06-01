from django.contrib import admin

from apps.integrations.models import PlatformConnection, SyncJob


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
