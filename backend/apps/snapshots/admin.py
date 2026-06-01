from django.contrib import admin

from apps.snapshots.models import PeilDatumSnapshot


@admin.register(PeilDatumSnapshot)
class PeilDatumSnapshotAdmin(admin.ModelAdmin):
    list_display = ("user", "year", "created_at")
    list_filter = ("year",)
    search_fields = ("user__email",)
    readonly_fields = ("user", "year", "data", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
