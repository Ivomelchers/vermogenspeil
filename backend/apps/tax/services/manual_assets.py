"""Handmatige box 3-schulden en vastgoed — aggregatie voor forfait en werkelijk."""

from decimal import Decimal, ROUND_HALF_UP

from apps.tax.models import Box3Debt, Box3RealEstate, Box3RealEstateType
from apps.tax.services.bijtelling import total_bijtelling


def _fmt(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def rental_value_for_property(prop: Box3RealEstate) -> Decimal:
    if prop.vacancy_ratio is not None:
        return (prop.value_eur * prop.vacancy_ratio).quantize(Decimal("0.01"))
    if prop.property_type in (Box3RealEstateType.RENTAL_NL, Box3RealEstateType.RENTAL_ABROAD):
        if prop.annual_rent_eur > 0 and prop.value_eur > 0:
            ratio = min(Decimal("1"), prop.annual_rent_eur / prop.value_eur)
            if ratio <= Decimal("0.01"):
                return (prop.value_eur * Decimal("0.73")).quantize(Decimal("0.01"))
            if ratio <= Decimal("0.02"):
                return (prop.value_eur * Decimal("0.79")).quantize(Decimal("0.01"))
            if ratio <= Decimal("0.03"):
                return (prop.value_eur * Decimal("0.84")).quantize(Decimal("0.01"))
            if ratio <= Decimal("0.04"):
                return (prop.value_eur * Decimal("0.90")).quantize(Decimal("0.01"))
            if ratio <= Decimal("0.05"):
                return (prop.value_eur * Decimal("0.95")).quantize(Decimal("0.01"))
        return prop.value_eur
    return prop.value_eur


def manual_box3_totals(user, year: int) -> dict[str, Decimal]:
    schulden = Decimal(0)
    overig = Decimal(0)
    buitenland = Decimal(0)

    for debt in Box3Debt.objects.filter(user=user, tax_year=year):
        schulden += debt.outstanding_eur

    for prop in Box3RealEstate.objects.filter(user=user, tax_year=year):
        value = rental_value_for_property(prop)
        overig += value
        if prop.is_abroad:
            buitenland += value

    return {
        "schulden": schulden,
        "overige_bezittingen": overig,
        "buitenlands_vastgoed": buitenland,
    }


def manual_werkelijk_extras(user, year: int) -> dict:
    huur = Decimal(0)
    rente_schulden = Decimal(0)

    for prop in Box3RealEstate.objects.filter(user=user, tax_year=year):
        huur += prop.rental_income_ytd_eur

    for debt in Box3Debt.objects.filter(user=user, tax_year=year):
        rente_schulden += debt.interest_paid_ytd_eur

    return {
        "huur": huur,
        "rente_schulden": rente_schulden,
        "bijtelling": total_bijtelling(user, year),
    }


def merge_box3_totals(portfolio_totals: dict[str, str], manual: dict[str, Decimal]) -> dict[str, str]:
    b = Decimal(portfolio_totals.get("banktegoeden_eur", "0")) + manual.get("banktegoeden", Decimal(0))
    o = Decimal(portfolio_totals.get("overige_bezittingen_eur", "0")) + manual.get(
        "overige_bezittingen", Decimal(0)
    )
    s = Decimal(portfolio_totals.get("schulden_eur", "0")) + manual.get("schulden", Decimal(0))
    return {
        "banktegoeden_eur": _fmt(b),
        "overige_bezittingen_eur": _fmt(o),
        "schulden_eur": _fmt(s),
        "buitenlands_vastgoed_eur": _fmt(manual.get("buitenlands_vastgoed", Decimal(0))),
    }
