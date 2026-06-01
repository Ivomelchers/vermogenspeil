from decimal import Decimal

from django.utils import timezone

from apps.integrations.models import PlatformConnection
from apps.portfolio.models import Portfolio
from apps.portfolio.services.returns import compute_return_summary
from apps.portfolio.services.valuation import asset_type_label, position_value_eur


def _decimal_str(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.01")), "f")


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
        }

    positions_qs = portfolio.positions.select_related("asset").order_by("-updated_at")
    position_rows = []
    category_totals: dict[str, Decimal] = {}
    total = Decimal(0)

    for position in positions_qs:
        value = position_value_eur(position)
        if value <= 0:
            continue

        total += value
        label = asset_type_label(position.asset.asset_type)
        category_totals[label] = category_totals.get(label, Decimal(0)) + value

        position_rows.append(
            {
                "id": position.id,
                "symbol": position.asset.symbol,
                "name": position.asset.name or position.asset.symbol,
                "asset_type": position.asset.asset_type,
                "category_label": label,
                "quantity": _decimal_str(position.quantity),
                "value_eur": _decimal_str(value),
            }
        )

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

    platforms = []
    for connection in PlatformConnection.objects.for_user(user).filter(is_active=True):
        platforms.append(
            {
                "id": connection.id,
                "display_name": connection.display_name,
                "platform": connection.platform,
                "platform_display": connection.get_platform_display(),
                "connection_method_display": connection.get_connection_method_display(),
                "status": connection.status,
                "is_demo": connection.is_demo,
                "last_synced_at": (
                    connection.last_synced_at.isoformat() if connection.last_synced_at else None
                ),
            }
        )

    returns = compute_return_summary(portfolio)

    return {
        "has_portfolio": True,
        "portfolio_id": portfolio.id,
        "portfolio_name": portfolio.name,
        "valuation_method": "cost_basis",
        "valuation_note": "Waarde op basis van kostprijs. Marktwaarden volgen met koersdata (fase 5).",
        "as_of": timezone.now().date().isoformat(),
        "total_value_eur": _decimal_str(total),
        "returns": {
            "invested_eur": _decimal_str(returns["invested_eur"]),
            "unrealized_return_eur": _decimal_str(returns["unrealized_return_eur"]),
            "unrealized_return_percent": _decimal_str(returns["unrealized_return_percent"]),
            "method": returns["method"],
            "note": returns["note"],
        },
        "positions": position_rows,
        "by_category": by_category,
        "platforms": platforms,
        "positions_count": len(position_rows),
        "transactions_count": portfolio.transactions.count(),
    }
