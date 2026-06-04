from django.contrib import admin

from apps.pricing.models import InstrumentMapping


@admin.register(InstrumentMapping)
class InstrumentMappingAdmin(admin.ModelAdmin):
    list_display = ("isin", "yahoo_ticker", "mic", "asset_type", "source", "updated_at")
    list_filter = ("source", "asset_type")
    search_fields = ("isin", "yahoo_ticker")
    readonly_fields = ("created_at", "updated_at")
