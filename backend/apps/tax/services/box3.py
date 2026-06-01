from decimal import Decimal

from apps.snapshots.models import PeilDatumSnapshot
from apps.tax.models import TaxYearParameter
from apps.tax.services.forfaitair import calculate_forfaitair
from apps.tax.services.parameters import TaxParametersNotFoundError, get_forfaitair_params
from apps.tax.services.snapshot_inputs import extract_box3_totals_from_snapshot_data


def build_forfaitair_summary(user, year: int) -> dict:
    snapshot = PeilDatumSnapshot.objects.filter(user=user, year=year).first()
    if not snapshot:
        return {
            "available": False,
            "year": year,
            "message": f"Geen peildatum-snapshot voor {year}. Leg eerst uw peildatum vast.",
        }

    try:
        params = get_forfaitair_params(year)
    except TaxParametersNotFoundError as exc:
        return {
            "available": False,
            "year": year,
            "message": str(exc),
        }

    totals = extract_box3_totals_from_snapshot_data(snapshot.data)
    b = Decimal(totals["banktegoeden_eur"])
    o = Decimal(totals["overige_bezittingen_eur"])
    s = Decimal(totals["schulden_eur"])

    result = calculate_forfaitair(
        banktegoeden=b,
        overige_bezittingen=o,
        schulden=s,
        params=params,
        has_fiscal_partner=getattr(user, "has_fiscal_partner", False),
    )

    param_row = TaxYearParameter.objects.get(year=year)

    return {
        "available": True,
        "year": year,
        "method": "forfaitair",
        "snapshot_id": snapshot.id,
        "snapshot_total_eur": snapshot.data.get("total_value_eur"),
        "parameters_provisional": not (
            param_row.banktegoeden_definitief and param_row.schulden_definitief
        ),
        "box3_inputs": totals,
        "calculation": result.as_dict(),
        "tax_due_eur": result.as_dict()["tax_due_eur"],
        "disclaimer": (
            "Forfaitaire Box 3 op basis van uw vastgelegde peildatum-snapshot. "
            "Geen vervanging van officiële aangifte."
        ),
    }
