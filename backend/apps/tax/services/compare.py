from decimal import Decimal


def compare_forfait_werkelijk(*, forfait_tax: Decimal, werkelijk_tax: Decimal) -> dict:
    besparing = forfait_tax - werkelijk_tax
    voordelig = besparing > 0
    recommended = "werkelijk" if voordelig else "forfaitair"
    applied_tax = min(forfait_tax, werkelijk_tax)

    if voordelig:
        message = f"Werkelijk rendement kan € {int(besparing)} besparen t.o.v. forfaitair."
    elif werkelijk_tax > forfait_tax:
        message = "Forfait blijft het voordeligst voor u dit jaar."
    else:
        message = "Forfait en werkelijk leiden tot hetzelfde bedrag."

    return {
        "forfait_tax_eur": str(int(forfait_tax)),
        "werkelijk_tax_eur": str(int(werkelijk_tax)),
        "applied_tax_eur": str(int(applied_tax)),
        "savings_eur": str(int(max(Decimal(0), besparing))),
        "werkelijk_is_beneficial": voordelig,
        "recommended_method": recommended,
        "message": message,
    }
