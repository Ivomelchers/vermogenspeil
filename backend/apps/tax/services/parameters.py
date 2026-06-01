from decimal import Decimal

from apps.tax.models import TaxYearParameter
from apps.tax.services.forfaitair import ForfaitairParams


class TaxParametersNotFoundError(Exception):
    pass


def params_from_model(row: TaxYearParameter) -> ForfaitairParams:
    return ForfaitairParams(
        pb=row.rendement_banktegoeden,
        po=row.rendement_overige_bezittingen,
        ps=row.rendement_schulden,
        tarief=row.tarief_box3,
        heffingsvrij=row.heffingsvrij_vermogen,
        schuldendrempel=row.schuldendrempel,
    )


def get_forfaitair_params(year: int) -> ForfaitairParams:
    row = TaxYearParameter.objects.filter(year=year).first()
    if not row:
        raise TaxParametersNotFoundError(f"Geen fiscale parameters voor belastingjaar {year}.")
    return params_from_model(row)


def ensure_default_parameters() -> None:
    """Idempotent seed voor 2026 (Ivo / Belastingdienst voorlopig)."""
    TaxYearParameter.objects.update_or_create(
        year=2026,
        defaults={
            "heffingsvrij_vermogen": Decimal("59357.00"),
            "rendement_banktegoeden": Decimal("0.012800"),
            "rendement_overige_bezittingen": Decimal("0.060000"),
            "rendement_schulden": Decimal("0.027000"),
            "schuldendrempel": Decimal("3800.00"),
            "tarief_box3": Decimal("0.360000"),
            "banktegoeden_definitief": False,
            "schulden_definitief": False,
            "notes": "Voorlopige percentages banktegoeden en schulden 2026.",
        },
    )
