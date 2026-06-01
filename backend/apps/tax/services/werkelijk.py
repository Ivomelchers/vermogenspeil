"""Werkelijk rendement Box 3 (Premium) — hoofdstuk 12 Ivo-spec."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from zoneinfo import ZoneInfo

from apps.portfolio.models import AssetType, Portfolio, Transaction, TransactionType
from apps.portfolio.services import get_or_create_default_portfolio
from apps.snapshots.models import PeilDatumSnapshot
from apps.tax.services.forfaitair import _money, _percent
from apps.tax.services.parameters import ForfaitairParams
from apps.tax.services.manual_assets import manual_werkelijk_extras
from apps.tax.services.portfolio_value import current_portfolio_value_eur

AMSTERDAM = ZoneInfo("Europe/Amsterdam")


@dataclass(frozen=True)
class WerkelijkResult:
    w_start: Decimal
    w_end: Decimal
    netto_inleg: Decimal
    reguliere_voordelen: Decimal
    dividend: Decimal
    rente_bank: Decimal
    huur: Decimal
    staking: Decimal
    overige_inkomsten: Decimal
    waardemutatie: Decimal
    bijtelling: Decimal
    rente_schulden: Decimal
    woz_investering: Decimal
    werkelijk_rendement: Decimal
    werkelijk_belastbaar: Decimal
    belasting: Decimal
    werkelijk_percent: Decimal

    def as_dict(self) -> dict:
        return {
            "w_start_eur": _money(self.w_start),
            "w_end_eur": _money(self.w_end),
            "netto_inleg_eur": _money(self.netto_inleg),
            "components": {
                "dividend_eur": _money(self.dividend),
                "rente_bank_eur": _money(self.rente_bank),
                "huur_eur": _money(self.huur),
                "staking_eur": _money(self.staking),
                "overige_inkomsten_eur": _money(self.overige_inkomsten),
                "reguliere_voordelen_eur": _money(self.reguliere_voordelen),
                "waardemutatie_eur": _money(self.waardemutatie),
                "bijtelling_eur": _money(self.bijtelling),
                "rente_schulden_eur": _money(self.rente_schulden),
                "woz_investering_eur": _money(self.woz_investering),
            },
            "werkelijk_rendement_eur": _money(self.werkelijk_rendement),
            "werkelijk_belastbaar_eur": _money(self.werkelijk_belastbaar),
            "tax_due_eur": _money(self.belasting, whole=True),
            "werkelijk_percent": _percent(self.werkelijk_percent),
        }


def _year_bounds(year: int) -> tuple[datetime, datetime]:
    return (
        datetime(year, 1, 1, 0, 0, 0, tzinfo=AMSTERDAM),
        datetime(year, 12, 31, 23, 59, 59, tzinfo=AMSTERDAM),
    )


def _tx_amount_eur(tx: Transaction) -> Decimal:
    if tx.total_eur is not None:
        return abs(Decimal(tx.total_eur))
    if tx.price_eur is not None:
        return abs(tx.quantity * Decimal(tx.price_eur))
    return abs(tx.quantity)


def _aggregate_year_transactions(portfolio: Portfolio, year: int) -> dict:
    start, end = _year_bounds(year)
    txs = portfolio.transactions.filter(
        occurred_at__gte=start,
        occurred_at__lte=end,
    ).select_related("asset")

    dividend = Decimal(0)
    rente_bank = Decimal(0)
    staking = Decimal(0)
    overige = Decimal(0)
    netto_inleg = Decimal(0)
    flow_rows = []

    for tx in txs:
        amount = _tx_amount_eur(tx)
        if tx.transaction_type == TransactionType.DIVIDEND:
            dividend += amount
        elif tx.transaction_type == TransactionType.DEPOSIT:
            netto_inleg += amount
            flow_rows.append({"type": "storting", "amount_eur": _money(amount), "date": tx.occurred_at.isoformat()})
        elif tx.transaction_type == TransactionType.WITHDRAWAL:
            netto_inleg -= amount
            flow_rows.append({"type": "opname", "amount_eur": _money(amount), "date": tx.occurred_at.isoformat()})
        elif tx.transaction_type == TransactionType.OTHER:
            if tx.asset.asset_type == AssetType.CASH:
                rente_bank += amount
            elif tx.asset.asset_type == AssetType.CRYPTO:
                staking += amount
            else:
                overige += amount

    return {
        "dividend": dividend,
        "rente_bank": rente_bank,
        "huur": Decimal(0),
        "staking": staking,
        "overige_inkomsten": overige,
        "netto_inleg": netto_inleg,
        "cashflows": flow_rows,
    }


def calculate_werkelijk(
    *,
    w_start: Decimal,
    w_end: Decimal,
    aggregates: dict,
    params: ForfaitairParams,
) -> WerkelijkResult:
    ni = aggregates["netto_inleg"]
    div = aggregates["dividend"]
    rnt_b = aggregates["rente_bank"]
    huur = aggregates.get("huur", Decimal(0))
    stk = aggregates["staking"]
    ink = aggregates["overige_inkomsten"]
    bijt = aggregates.get("bijtelling", Decimal(0))
    rnt_s = aggregates.get("rente_schulden", Decimal(0))
    inv_woz = aggregates.get("woz_investering", Decimal(0))

    reg = div + rnt_b + huur + stk + ink
    wm = (w_end - w_start) - ni
    wr = reg + wm + bijt - rnt_s - inv_woz
    wr_belastbaar = max(Decimal(0), wr)
    belasting = (wr_belastbaar * params.tarief).quantize(Decimal("1"), rounding=ROUND_HALF_UP)

    w_gem = (w_start + w_end) / 2
    wr_pct = (wr / w_gem * Decimal(100)) if w_gem > 0 else Decimal(0)

    return WerkelijkResult(
        w_start=w_start,
        w_end=w_end,
        netto_inleg=ni,
        reguliere_voordelen=reg,
        dividend=div,
        rente_bank=rnt_b,
        huur=huur,
        staking=stk,
        overige_inkomsten=ink,
        waardemutatie=wm,
        bijtelling=bijt,
        rente_schulden=rnt_s,
        woz_investering=inv_woz,
        werkelijk_rendement=wr,
        werkelijk_belastbaar=wr_belastbaar,
        belasting=belasting,
        werkelijk_percent=wr_pct,
    )


def build_werkelijk_summary(user, year: int, *, params: ForfaitairParams) -> dict:
    snapshot = PeilDatumSnapshot.objects.filter(user=user, year=year).first()
    if not snapshot:
        return {
            "available": False,
            "year": year,
            "message": f"Geen peildatum-snapshot voor {year}.",
        }

    portfolio = (
        Portfolio.objects.for_user(user).filter(is_default=True).first()
        or get_or_create_default_portfolio(user)
    )

    w_start = Decimal(str(snapshot.data.get("total_value_eur", "0")))
    w_end = current_portfolio_value_eur(portfolio)
    aggregates = _aggregate_year_transactions(portfolio, year)
    extras = manual_werkelijk_extras(user, year)
    aggregates["huur"] = aggregates.get("huur", Decimal(0)) + extras["huur"]
    aggregates["rente_schulden"] = extras["rente_schulden"]
    aggregates["bijtelling"] = extras["bijtelling"]
    result = calculate_werkelijk(w_start=w_start, w_end=w_end, aggregates=aggregates, params=params)

    now = datetime.now(tz=AMSTERDAM)
    is_provisional = now.year == year and (now.month < 12 or now.day < 31)

    return {
        "available": True,
        "year": year,
        "method": "werkelijk",
        "is_provisional": is_provisional,
        "provisional_note": (
            f"Voorlopige berekening t/m vandaag; definitief op 31-12-{year}."
            if is_provisional
            else f"Gebaseerd op waarden t/m einde {year}."
        ),
        "calculation": result.as_dict(),
        "tax_due_eur": result.as_dict()["tax_due_eur"],
        "cashflows": aggregates["cashflows"],
        "disclaimer": (
            "Werkelijk rendement: geen heffingsvrij vermogen, kosten niet aftrekbaar. "
            "Indicatief — geen vervanging van officiële aangifte."
        ),
    }
