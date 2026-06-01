"""Optionele fiscale waarschuwingen (geen product-roadmap in UI)."""

from apps.tax.models import TaxYearParameter


def build_tax_warnings(*, year: int, forfaitair: dict) -> list[str]:
    """Alleen Belastingdienst-/parameter-meldingen, geen interne scope-lijsten."""
    warnings: list[str] = []
    params_row = TaxYearParameter.objects.filter(year=year).first()

    if params_row is None:
        warnings.append(
            f"Fiscale parameters voor belastingjaar {year} zijn nog niet beschikbaar."
        )
    elif forfaitair.get("parameters_provisional"):
        warnings.append(
            "De percentages voor banktegoeden en schulden zijn nog voorlopig (Belastingdienst)."
        )

    return warnings
