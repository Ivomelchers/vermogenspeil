from datetime import datetime
from zoneinfo import ZoneInfo

from apps.portfolio.models import Portfolio, Transaction
from apps.portfolio.services import get_or_create_default_portfolio
from apps.snapshots.models import PeilDatumSnapshot
from apps.tax.services.box3 import build_forfaitair_summary
from apps.tax.services.compare import compare_forfait_werkelijk
from apps.tax.services.parameters import get_forfaitair_params
from apps.tax.models import Box3BankBalance, Box3Debt, Box3RealEstate
from apps.tax.serializers import (
    Box3BankBalanceSerializer,
    Box3DebtSerializer,
    Box3RealEstateSerializer,
)
from apps.tax.services.tax_year import tax_year_context
from apps.tax.services.werkelijk import build_werkelijk_summary


def build_box3_report(user, year: int, *, include_werkelijk: bool) -> dict:
    forfait = build_forfaitair_summary(user, year)
    snapshot = PeilDatumSnapshot.objects.filter(user=user, year=year).first()

    portfolio = (
        Portfolio.objects.for_user(user).filter(is_default=True).first()
        or get_or_create_default_portfolio(user)
    )

    positions_start = []
    positions_end = []
    if snapshot:
        for row in snapshot.data.get("positions") or []:
            positions_start.append(
                {
                    "symbol": row.get("symbol"),
                    "value_eur": row.get("value_eur"),
                    "quantity": row.get("quantity"),
                    "valuation_source": row.get("valuation_source"),
                }
            )

    for position in portfolio.positions.select_related("asset"):
        from apps.portfolio.services.valuation import position_value_eur

        value, source = position_value_eur(position)
        positions_end.append(
            {
                "symbol": position.asset.symbol,
                "quantity": str(position.quantity),
                "value_eur": str(value),
                "valuation_source": source,
            }
        )

    income_events = []
    start = datetime(year, 1, 1, tzinfo=ZoneInfo("Europe/Amsterdam"))
    end = datetime(year, 12, 31, 23, 59, 59, tzinfo=ZoneInfo("Europe/Amsterdam"))
    for tx in portfolio.transactions.filter(
        occurred_at__gte=start,
        occurred_at__lte=end,
        transaction_type__in=["dividend", "deposit", "withdrawal", "other"],
    ).select_related("asset"):
        income_events.append(
            {
                "date": tx.occurred_at.date().isoformat(),
                "symbol": tx.asset.symbol,
                "type": tx.transaction_type,
                "total_eur": str(tx.total_eur) if tx.total_eur is not None else None,
                "source_platform": tx.source_platform,
            }
        )

    report = {
        "year": year,
        "generated_at": datetime.now(tz=ZoneInfo("Europe/Amsterdam")).isoformat(),
        "forfaitair": forfait,
        "positions_start": positions_start,
        "positions_end": positions_end,
        "income_and_cashflows": income_events,
        "bank_balances": Box3BankBalanceSerializer(
            Box3BankBalance.objects.filter(user=user, tax_year=year),
            many=True,
        ).data,
        "debts": Box3DebtSerializer(
            Box3Debt.objects.filter(user=user, tax_year=year),
            many=True,
        ).data,
        "real_estate": Box3RealEstateSerializer(
            Box3RealEstate.objects.filter(user=user, tax_year=year),
            many=True,
        ).data,
        "tax_year_context": tax_year_context(),
    }

    if include_werkelijk and user.is_premium:
        params = get_forfaitair_params(year)
        werkelijk = build_werkelijk_summary(user, year, params=params)
        report["werkelijk"] = werkelijk
        if forfait.get("available") and werkelijk.get("available"):
            from decimal import Decimal

            report["comparison"] = compare_forfait_werkelijk(
                forfait_tax=Decimal(forfait["tax_due_eur"]),
                werkelijk_tax=Decimal(werkelijk["tax_due_eur"]),
            )
    else:
        report["werkelijk"] = {
            "available": False,
            "message": "Werkelijk rendement niet opgenomen in dit rapport.",
        }

    return report
