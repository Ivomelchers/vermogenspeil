from django.contrib import admin

from apps.tax.models import TaxYearParameter


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
