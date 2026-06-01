from django.contrib import admin

from apps.portfolio.models import Asset, Portfolio, Position, Transaction


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("name", "user", "is_default", "updated_at")
    list_filter = ("is_default",)
    search_fields = ("name", "user__email")


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ("symbol", "user", "asset_type", "category")
    search_fields = ("symbol", "user__email")


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "asset", "quantity", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = (
        "portfolio",
        "asset",
        "transaction_type",
        "quantity",
        "occurred_at",
        "source_platform",
    )
    list_filter = ("transaction_type", "source_platform")
