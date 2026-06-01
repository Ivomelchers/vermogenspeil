from django.contrib import admin

from apps.tax.models import Box3Debt, Box3RealEstate, TaxYearParameter


@admin.register(TaxYearParameter)
class TaxYearParameterAdmin(admin.ModelAdmin):
    list_display = (
        "year",
        "heffingsvrij_vermogen",
        "tarief_box3",
        "rendement_banktegoeden",
        "rendement_overige_bezittingen",
        "banktegoeden_definitief",
    )
    ordering = ("-year",)


@admin.register(Box3Debt)
class Box3DebtAdmin(admin.ModelAdmin):
    list_display = ("user", "tax_year", "label", "outstanding_eur", "interest_paid_ytd_eur")
    list_filter = ("tax_year", "debt_type")


@admin.register(Box3RealEstate)
class Box3RealEstateAdmin(admin.ModelAdmin):
    list_display = ("user", "tax_year", "label", "value_eur", "is_abroad", "property_type")
    list_filter = ("tax_year", "is_abroad", "property_type")
