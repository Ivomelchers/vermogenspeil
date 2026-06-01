import logging
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.portfolio.models import Portfolio, VermogensCategorie
from apps.portfolio.services.historical_valuation import portfolio_valuation_at_date
from apps.portfolio.services.valuation import asset_type_label
from apps.snapshots.exceptions import SnapshotAlreadyExistsError
from apps.snapshots.models import PeilDatumSnapshot
from apps.tax.services.snapshot_inputs import box3_totals_from_category

logger = logging.getLogger(__name__)
User = get_user_model()
AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def peildatum_instant_cet(year: int) -> datetime:
    """1 januari 00:00 in Europe/Amsterdam (CET/CEST — TRAP 1)."""
    return datetime(year, 1, 1, 0, 0, 0, tzinfo=AMSTERDAM)


def peildatum_date_for_year(year: int) -> date:
    return date(year, 1, 1)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def build_peildatum_payload(user, year: int) -> dict:
    portfolio = (
        Portfolio.objects.for_user(user).filter(is_default=True).first()
        or Portfolio.objects.for_user(user).first()
    )

    peildatum = peildatum_instant_cet(year)
    on_date = peildatum_date_for_year(year)
    captured_at = timezone.now()

    if not portfolio:
        return {
            "year": year,
            "peildatum": peildatum.isoformat(),
            "captured_at": captured_at.isoformat(),
            "timezone": "Europe/Amsterdam",
            "has_portfolio": False,
            "valuation_method": "cost_basis",
            "valuation_at_peildatum": "empty",
            "total_value_eur": "0.00",
            "positions": [],
            "by_category": [],
            "box3_totals": {
                "banktegoeden_eur": "0.00",
                "overige_bezittingen_eur": "0.00",
                "schulden_eur": "0.00",
            },
            "note": (
                "Geen portefeuille bij vastlegging. Leg eerst posities vast of koppel een platform."
            ),
        }

    valuation = portfolio_valuation_at_date(portfolio, on_date)

    position_rows = []
    category_totals: dict[str, Decimal] = {}
    box3_totals = {
        "banktegoeden": Decimal(0),
        "overige_bezittingen": Decimal(0),
        "schulden": Decimal(0),
    }
    total = valuation["total_value_eur"]

    for row in valuation["positions"]:
        position = row["position"]
        value = row["value_eur"]
        fiscale = position.asset.category
        box3_totals_from_category(fiscale, value, box3_totals)

        label = asset_type_label(position.asset.asset_type)
        category_totals[label] = category_totals.get(label, Decimal(0)) + value

        position_row = {
            "symbol": position.asset.symbol,
            "name": position.asset.name or position.asset.symbol,
            "asset_type": position.asset.asset_type,
            "fiscale_category": fiscale,
            "category_label": label,
            "quantity": _decimal_str(row["quantity"]),
            "value_eur": _decimal_str(value),
            "valuation_source": row["valuation_source"],
        }
        if row.get("unit_price_eur"):
            position_row["unit_price_eur"] = _decimal_str(row["unit_price_eur"])
        position_rows.append(position_row)

    by_category = []
    if total > 0:
        for label, amount in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
            percent = (amount / total) * Decimal(100)
            by_category.append(
                {
                    "label": label,
                    "value_eur": _decimal_str(amount),
                    "share_percent": _decimal_str(percent),
                }
            )

    method_note = {
        "historical_prices": "Waarden op 1 januari via historische koersen.",
        "mixed_historical": (
            "Waarden op 1 januari: deels historische koersen, deels kostprijs als fallback."
        ),
        "cost_basis_fallback": (
            "Geen historische koers beschikbaar; kostprijs gebruikt als fallback op 1 januari."
        ),
        "empty": "Geen posities met waarde op de peildatum.",
    }

    return {
        "year": year,
        "peildatum": peildatum.isoformat(),
        "captured_at": captured_at.isoformat(),
        "timezone": "Europe/Amsterdam",
        "has_portfolio": True,
        "portfolio_id": portfolio.id,
        "valuation_method": valuation["valuation_method"],
        "valuation_at_peildatum": valuation["valuation_method"],
        "historical_priced_count": valuation["historical_priced"],
        "positions_count": valuation["total_positions"],
        "total_value_eur": _decimal_str(total),
        "positions": position_rows,
        "by_category": by_category,
        "box3_totals": {
            "banktegoeden_eur": _decimal_str(box3_totals["banktegoeden"]),
            "overige_bezittingen_eur": _decimal_str(box3_totals["overige_bezittingen"]),
            "schulden_eur": _decimal_str(box3_totals["schulden"]),
        },
        "note": method_note.get(
            valuation["valuation_method"],
            "Peildatum-waardering op 1 januari.",
        ),
    }


def create_peildatum_snapshot(user, year: int) -> PeilDatumSnapshot:
    if PeilDatumSnapshot.objects.filter(user=user, year=year).exists():
        raise SnapshotAlreadyExistsError(
            f"Peildatum-snapshot voor {year} bestaat al. Gebruik herberekening of verwijder niet."
        )

    payload = build_peildatum_payload(user, year)
    payload["recalculated_at"] = None
    return PeilDatumSnapshot.objects.create(user=user, year=year, data=payload)


def create_peildatum_snapshots_for_all_users(year: int) -> dict:
    created = 0
    skipped = 0
    errors = 0

    for user in User.objects.filter(is_active=True).iterator():
        try:
            create_peildatum_snapshot(user, year)
            created += 1
        except SnapshotAlreadyExistsError:
            skipped += 1
        except Exception:
            errors += 1
            logger.exception("Peildatum-snapshot mislukt voor user %s", user.pk)

    return {"year": year, "created": created, "skipped": skipped, "errors": errors}
