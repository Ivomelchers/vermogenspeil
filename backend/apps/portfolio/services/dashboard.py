from decimal import Decimal

from django.utils import timezone

from apps.integrations.models import PlatformConnection
from apps.integrations.services.demo_seed import demo_features_enabled
from apps.portfolio.models import Portfolio
from apps.portfolio.services.returns import compute_return_summary
from apps.portfolio.services.valuation import (
    asset_type_label,
    fetch_live_prices_for_positions,
    position_value_eur,
)
from apps.portfolio.services.value_history import compute_value_history
from apps.portfolio.services.ytd import compute_ytd_summary


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


def _valuation_note(method: str) -> str:
    notes = {
        "market": "Waarde op basis van live marktprijzen (cache 15 min).",
        "mixed": "Deels marktwaarde, deels kostprijs waar geen koers beschikbaar is.",
        "cost_basis": "Waarde op basis van kostprijs — geen live koersen beschikbaar.",
    }
    return notes.get(method, notes["cost_basis"])


def build_dashboard_summary(user) -> dict:
    portfolio = (
        Portfolio.objects.for_user(user).filter(is_default=True).first()
        or Portfolio.objects.for_user(user).first()
    )

    if not portfolio:
        return {
            "has_portfolio": False,
            "valuation_method": "cost_basis",
            "as_of": timezone.now().date().isoformat(),
            "total_value_eur": "0.00",
            "positions": [],
            "by_category": [],
            "platforms": [],
            "positions_count": 0,
            "transactions_count": 0,
            "recent_activity": [],
            "value_history": [],
        }

    positions_qs = list(portfolio.positions.select_related("asset").order_by("-updated_at"))
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
            "id": position.id,
            "asset_id": position.asset_id,
            "category": position.asset.category,
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
            row["price_source"] = live_prices[symbol_key].source
        position_rows.append(row)

    position_rows.sort(key=lambda row: Decimal(row["value_eur"]), reverse=True)

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

    show_demo = demo_features_enabled()
    platforms = []
    connections_qs = PlatformConnection.objects.for_user(user).filter(is_active=True)
    if not show_demo:
        connections_qs = connections_qs.filter(is_demo=False)

    for connection in connections_qs:
        platforms.append(
            {
                "id": connection.id,
                "display_name": connection.display_name,
                "platform": connection.platform,
                "platform_display": connection.get_platform_display(),
                "connection_method_display": connection.get_connection_method_display(),
                "status": connection.status,
                "last_synced_at": (
                    connection.last_synced_at.isoformat() if connection.last_synced_at else None
                ),
            }
        )

    valuation_method = _resolve_valuation_method(market_count, len(position_rows))
    returns = compute_return_summary(portfolio, live_prices=live_prices)
    ytd = compute_ytd_summary(portfolio, user)
    ytd_start_eur = None
    ytd_start_date = None
    if ytd.get("available"):
        ytd_start_eur = Decimal(str(ytd.get("start_value_eur", "0")))
        ytd_start_date = ytd.get("start_as_of")

    value_history = compute_value_history(
        portfolio,
        current_value_eur=total,
        ytd_start_eur=ytd_start_eur,
        ytd_start_date=ytd_start_date,
    )

    recent_activity = []
    for tx in (
        portfolio.transactions.select_related("asset")
        .order_by("-occurred_at", "-id")[:8]
    ):
        amount = tx.total_eur
        if amount is None and tx.price_eur is not None:
            amount = tx.quantity * tx.price_eur
        recent_activity.append(
            {
                "id": tx.id,
                "occurred_at": tx.occurred_at.isoformat(),
                "symbol": tx.asset.symbol,
                "transaction_type": tx.transaction_type,
                "transaction_type_label": tx.get_transaction_type_display(),
                "source_platform": tx.source_platform,
                "quantity": _decimal_str(tx.quantity),
                "total_eur": _decimal_str(amount) if amount is not None else None,
            }
        )

    return {
        "has_portfolio": True,
        "portfolio_id": portfolio.id,
        "portfolio_name": portfolio.name,
        "valuation_method": valuation_method,
        "valuation_note": _valuation_note(valuation_method),
        "prices_cached": bool(live_prices),
        "as_of": timezone.now().date().isoformat(),
        "total_value_eur": _decimal_str(total),
        "returns": {
            "invested_eur": _decimal_str(returns["invested_eur"]),
            "unrealized_return_eur": _decimal_str(returns["unrealized_return_eur"]),
            "unrealized_return_percent": _decimal_str(returns["unrealized_return_percent"]),
            "method": returns["method"],
            "note": returns["note"],
        },
        "ytd": ytd,
        "positions": position_rows,
        "by_category": by_category,
        "platforms": platforms,
        "positions_count": len(position_rows),
        "transactions_count": portfolio.transactions.count(),
        "recent_activity": recent_activity,
        "value_history": value_history,
    }
