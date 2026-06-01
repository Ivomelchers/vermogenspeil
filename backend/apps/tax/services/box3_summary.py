from decimal import Decimal

from apps.tax.services.box3 import build_forfaitair_summary
from apps.tax.services.compare import compare_forfait_werkelijk
from apps.tax.services.parameters import TaxParametersNotFoundError, get_forfaitair_params
from apps.tax.services.tax_year import tax_year_context
from apps.tax.services.transparency import build_tax_warnings
from apps.tax.services.werkelijk import build_werkelijk_summary


def build_box3_summary(user, year: int) -> dict:
    forfait = build_forfaitair_summary(user, year)
    is_premium = getattr(user, "is_premium", False)

    try:
        params = get_forfaitair_params(year)
    except TaxParametersNotFoundError as exc:
        return {
            "year": year,
            "forfaitair": forfait,
            "werkelijk": {"available": False, "message": str(exc)},
            "comparison": None,
            "is_premium": is_premium,
            "applied_tax_eur": None,
            "message": str(exc),
        }

    werkelijk = {"available": False, "message": "Werkelijk rendement is niet beschikbaar."}
    if is_premium:
        werkelijk = build_werkelijk_summary(user, year, params=params)

    comparison = None
    applied_tax = None
    if forfait.get("available") and forfait.get("tax_due_eur") is not None:
        forfait_tax = Decimal(forfait["tax_due_eur"])
        if werkelijk.get("available") and werkelijk.get("tax_due_eur") is not None:
            werkelijk_tax = Decimal(werkelijk["tax_due_eur"])
            comparison = compare_forfait_werkelijk(
                forfait_tax=forfait_tax,
                werkelijk_tax=werkelijk_tax,
            )
            applied_tax = comparison["applied_tax_eur"]
        else:
            applied_tax = str(int(forfait_tax))

    return {
        "year": year,
        "tax_year_context": tax_year_context(),
        "is_premium": is_premium,
        "forfaitair": forfait,
        "werkelijk": werkelijk,
        "comparison": comparison,
        "applied_tax_eur": applied_tax,
        "tax_warnings": build_tax_warnings(year=year, forfaitair=forfait),
        "message": (
            "Belastingdienst past automatisch het laagste bedrag toe (forfaitair vs. werkelijk)."
            if comparison
            else forfait.get("message", "")
        ),
    }
