"""Forfaitaire Box 3-berekening — zes stappen (Belastingdienst 2026)."""

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_UP


@dataclass(frozen=True)
class ForfaitairParams:
    pb: Decimal
    po: Decimal
    ps: Decimal
    tarief: Decimal
    heffingsvrij: Decimal
    schuldendrempel: Decimal


@dataclass(frozen=True)
class ForfaitairResult:
    banktegoeden: Decimal
    overige_bezittingen: Decimal
    schulden: Decimal
    schulden_aftrekbaar: Decimal
    rendement_bank: Decimal
    rendement_overig: Decimal
    rendement_schulden: Decimal
    belastbaar_rendement: Decimal
    rendementsgrondslag: Decimal
    grondslag_sparen_beleggen: Decimal
    aandeel_percent: Decimal
    voordeel: Decimal
    belasting_bruto: Decimal
    aftrek_dubbele_belasting: Decimal
    belasting_netto: Decimal

    def as_dict(self) -> dict:
        return {
            "inputs": {
                "banktegoeden_eur": _money(self.banktegoeden),
                "overige_bezittingen_eur": _money(self.overige_bezittingen),
                "schulden_eur": _money(self.schulden),
            },
            "steps": {
                "schulden_aftrekbaar_eur": _money(self.schulden_aftrekbaar),
                "rendement_bank_eur": _money(self.rendement_bank),
                "rendement_overig_eur": _money(self.rendement_overig),
                "rendement_schulden_eur": _money(self.rendement_schulden),
                "belastbaar_rendement_eur": _money(self.belastbaar_rendement),
                "rendementsgrondslag_eur": _money(self.rendementsgrondslag),
                "grondslag_sparen_beleggen_eur": _money(self.grondslag_sparen_beleggen),
                "aandeel_percent": _percent(self.aandeel_percent),
                "voordeel_eur": _money(self.voordeel),
                "belasting_bruto_eur": _money(self.belasting_bruto, whole=True),
                "aftrek_dubbele_belasting_eur": _money(self.aftrek_dubbele_belasting, whole=True),
                "belasting_netto_eur": _money(self.belasting_netto, whole=True),
            },
            "tax_due_eur": _money(self.belasting_netto, whole=True),
        }


def _money(value: Decimal, *, whole: bool = False) -> str:
    if whole:
        return str(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def _percent(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), "f")


def calculate_forfaitair(
    *,
    banktegoeden: Decimal,
    overige_bezittingen: Decimal,
    schulden: Decimal,
    params: ForfaitairParams,
    has_fiscal_partner: bool = False,
    buitenlands_vastgoed_overig: Decimal = Decimal(0),
) -> ForfaitairResult:
    """
    Zes stappen forfaitair Box 3. Aandeel% met 2 decimalen naar beneden (BD-voorbeeld).
    """
    b = Decimal(banktegoeden)
    o = Decimal(overige_bezittingen)
    s = Decimal(schulden)

    hf = params.heffingsvrij * (2 if has_fiscal_partner else 1)
    sd = params.schuldendrempel * (2 if has_fiscal_partner else 1)

    saf = max(Decimal(0), s - sd)
    rb = b * params.pb
    ro = o * params.po
    rs = saf * params.ps
    r = rb + ro - rs

    rg = b + o - saf
    gsb = max(Decimal(0), rg - hf)

    if gsb == 0 or rg == 0:
        return ForfaitairResult(
            banktegoeden=b,
            overige_bezittingen=o,
            schulden=s,
            schulden_aftrekbaar=saf,
            rendement_bank=rb,
            rendement_overig=ro,
            rendement_schulden=rs,
            belastbaar_rendement=r,
            rendementsgrondslag=rg,
            grondslag_sparen_beleggen=gsb,
            aandeel_percent=Decimal(0),
            voordeel=Decimal(0),
            belasting_bruto=Decimal(0),
            aftrek_dubbele_belasting=Decimal(0),
            belasting_netto=Decimal(0),
        )

    aandeel = (gsb / rg * Decimal(100)).quantize(Decimal("0.01"), rounding=ROUND_DOWN)
    voordeel = (r * aandeel / Decimal(100)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    belasting = (voordeel * params.tarief).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    o_buiten = max(Decimal(0), buitenlands_vastgoed_overig)
    aftrek = Decimal(0)
    if o_buiten > 0 and rg > 0:
        aftrek = (o_buiten / rg * belasting).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    netto = max(Decimal(0), belasting - aftrek)

    return ForfaitairResult(
        banktegoeden=b,
        overige_bezittingen=o,
        schulden=s,
        schulden_aftrekbaar=saf,
        rendement_bank=rb,
        rendement_overig=ro,
        rendement_schulden=rs,
        belastbaar_rendement=r,
        rendementsgrondslag=rg,
        grondslag_sparen_beleggen=gsb,
        aandeel_percent=aandeel,
        voordeel=voordeel,
        belasting_bruto=belasting,
        aftrek_dubbele_belasting=aftrek,
        belasting_netto=netto,
    )
