import logging
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.portfolio.models import Portfolio
from apps.portfolio.services.valuation import (
    asset_type_label,
    fetch_live_prices_for_positions,
    position_value_eur,
)
from apps.snapshots.exceptions import SnapshotAlreadyExistsError
from apps.snapshots.models import PeilDatumSnapshot

logger = logging.getLogger(__name__)
User = get_user_model()
AMSTERDAM = ZoneInfo("Europe/Amsterdam")


def peildatum_instant_cet(year: int) -> datetime:
    """1 januari 00:00 in Europe/Amsterdam (CET/CEST — TRAP 1)."""
    return datetime(year, 1, 1, 0, 0, 0, tzinfo=AMSTERDAM)


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


def _resolve_valuation_method(market_count: int, total_positions: int) -> str:
    if total_positions == 0:
        return "cost_basis"
    if market_count == total_positions:
        return "market"
    if market_count > 0:
        return "mixed"
    return "cost_basis"


def build_peildatum_payload(user, year: int) -> dict:
    portfolio = (
        Portfolio.objects.for_user(user).filter(is_default=True).first()
        or Portfolio.objects.for_user(user).first()
    )

    peildatum = peildatum_instant_cet(year)
    captured_at = timezone.now()

    if not portfolio:
        return {
            "year": year,
            "peildatum": peildatum.isoformat(),
            "captured_at": captured_at.isoformat(),
            "timezone": "Europe/Amsterdam",
            "has_portfolio": False,
            "valuation_method": "cost_basis",
            "total_value_eur": "0.00",
            "positions": [],
            "by_category": [],
            "note": (
                "Geen portefeuille bij vastlegging. Handmatige snapshot gebruikt "
                "huidige waardering als proxy."
            ),
        }

    positions_qs = list(portfolio.positions.select_related("asset"))
    live_prices = fetch_live_prices_for_positions(positions_qs)

    position_rows = []
    category_totals: dict[str, Decimal] = {}
    total = Decimal(0)
    market_count = 0

    for position in positions_qs:
        value, source = position_value_eur(position, live_prices=live_prices)
        if value <= 0:
            continue
        if source == "market":
            market_count += 1
        total += value
        label = asset_type_label(position.asset.asset_type)
        category_totals[label] = category_totals.get(label, Decimal(0)) + value

        row = {
            "symbol": position.asset.symbol,
            "name": position.asset.name or position.asset.symbol,
            "asset_type": position.asset.asset_type,
            "category_label": label,
            "quantity": _decimal_str(position.quantity),
            "value_eur": _decimal_str(value),
            "valuation_source": source,
        }
        symbol_key = position.asset.symbol.upper()
        if symbol_key in live_prices:
            row["unit_price_eur"] = _decimal_str(live_prices[symbol_key].price_eur)
        position_rows.append(row)

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

    valuation_method = _resolve_valuation_method(market_count, len(position_rows))

    return {
        "year": year,
        "peildatum": peildatum.isoformat(),
        "captured_at": captured_at.isoformat(),
        "timezone": "Europe/Amsterdam",
        "has_portfolio": True,
        "portfolio_id": portfolio.id,
        "valuation_method": valuation_method,
        "total_value_eur": _decimal_str(total),
        "positions": position_rows,
        "by_category": by_category,
        "positions_count": len(position_rows),
        "note": (
            "Snapshot vastgelegd op moment van aanmaken. "
            "Peildatum-tijdstip is 1 jan 00:00 CET; waarden zijn actuele koersen/kostprijs op capture-moment."
        ),
    }


def create_peildatum_snapshot(user, year: int) -> PeilDatumSnapshot:
    if PeilDatumSnapshot.objects.filter(user=user, year=year).exists():
        raise SnapshotAlreadyExistsError(
            f"Peildatum-snapshot voor {year} bestaat al en kan niet worden overschreven."
        )

    payload = build_peildatum_payload(user, year)
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
