"""Bijtelling eigen gebruik 2e woning — hoofdstuk 12."""

from decimal import Decimal

from apps.tax.models import BijtellingMethod, Box3RealEstate

DEFAULT_BIJTELLING_RATE = Decimal("0.0506")


def eigen_gebruik_days(property_obj: Box3RealEstate) -> int:
    if property_obj.eigen_gebruik_days > 0:
        return property_obj.eigen_gebruik_days
    days = 365 - property_obj.verhuur_days - property_obj.verbouw_days
    return max(0, min(365, days))


def bijtelling_for_property(property_obj: Box3RealEstate, *, year: int) -> Decimal:
    d_eigen = eigen_gebruik_days(property_obj)
    if d_eigen <= 0 or not property_obj.bijtelling_method:
        return Decimal(0)

    if property_obj.bijtelling_method == BijtellingMethod.HUURWAARDE:
        hw = property_obj.economic_rent_yearly_eur
        return (hw * Decimal(d_eigen) / Decimal(365)).quantize(Decimal("0.01"))

    rate = property_obj.bijtelling_rate or DEFAULT_BIJTELLING_RATE
    woz = property_obj.woz_previous_year_eur or property_obj.value_eur
    return (rate * woz * Decimal(d_eigen) / Decimal(365)).quantize(Decimal("0.01"))


def total_bijtelling(user, year: int) -> Decimal:
    total = Decimal(0)
    for prop in Box3RealEstate.objects.filter(user=user, tax_year=year):
        total += bijtelling_for_property(prop, year=year)
    return total
