from decimal import Decimal, InvalidOperation

from apps.portfolio.models import VermogensCategorie


def _parse_decimal(value) -> Decimal:
    if value is None:
        return Decimal(0)
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal(0)


def box3_totals_from_category(category: str, amount: Decimal, totals: dict[str, Decimal]) -> None:
    if category == VermogensCategorie.BANKTEGOED:
        totals["banktegoeden"] += amount
    elif category == VermogensCategorie.SCHULD:
        totals["schulden"] += amount
    else:
        totals["overige_bezittingen"] += amount


def extract_box3_totals_from_snapshot_data(data: dict) -> dict[str, str]:
    """
    B/O/S uit snapshot payload.
    Prefer `box3_totals`; fallback: sommeer posities met `fiscale_category`.
    """
    if boxed := data.get("box3_totals"):
        return {
            "banktegoeden_eur": str(boxed.get("banktegoeden_eur", "0.00")),
            "overige_bezittingen_eur": str(boxed.get("overige_bezittingen_eur", "0.00")),
            "schulden_eur": str(boxed.get("schulden_eur", "0.00")),
        }

    totals = {
        "banktegoeden": Decimal(0),
        "overige_bezittingen": Decimal(0),
        "schulden": Decimal(0),
    }

    for position in data.get("positions") or []:
        amount = _parse_decimal(position.get("value_eur"))
        category = position.get("fiscale_category") or VermogensCategorie.BELEGGING
        box3_totals_from_category(category, amount, totals)

    if not data.get("positions") and data.get("by_category"):
        for row in data["by_category"]:
            label = (row.get("label") or "").lower()
            amount = _parse_decimal(row.get("value_eur"))
            if "sparen" in label or "bank" in label:
                totals["banktegoeden"] += amount
            else:
                totals["overige_bezittingen"] += amount

    from decimal import ROUND_HALF_UP

    def fmt(d: Decimal) -> str:
        return format(d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")

    return {
        "banktegoeden_eur": fmt(totals["banktegoeden"]),
        "overige_bezittingen_eur": fmt(totals["overige_bezittingen"]),
        "schulden_eur": fmt(totals["schulden"]),
    }
