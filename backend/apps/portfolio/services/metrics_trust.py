"""Of dashboard-cijfers (inleg, YTD) betrouwbaar genoeg zijn om te tonen."""

from decimal import Decimal

from apps.portfolio.models import AssetType, Portfolio, TransactionType
from apps.portfolio.services.transaction_amounts import transaction_buy_cash_outflow
from apps.portfolio.services.valuation import position_value_eur
from apps.pricing.services import PriceQuote

# Waarschuw alleen als >5% portefeuillewaarde geen marktprijs heeft
MISSING_PRICE_VALUE_SHARE_THRESHOLD = Decimal("0.05")


def build_metrics_trust(
    portfolio: Portfolio,
    *,
    live_prices: dict[str, PriceQuote],
    valuation_method: str,
    ytd: dict,
) -> dict:
    """
    Waarschuwingen wanneer koersen ontbreken of YTD start/huidig niet vergelijkbaar is.
    """
    warnings: list[str] = []
    missing_price_symbols: list[str] = []
    missing_price_value = Decimal(0)
    total_position_value = Decimal(0)

    for position in portfolio.positions.select_related("asset"):
        if position.quantity <= 0:
            continue
        asset = position.asset
        if asset.asset_type == AssetType.CASH:
            continue
        value, source = position_value_eur(position, live_prices=live_prices)
        if value <= 0:
            continue
        total_position_value += value
        symbol = asset.symbol.upper()
        if symbol not in live_prices or source != "market":
            missing_price_symbols.append(symbol)
            missing_price_value += value

    missing_share = (
        (missing_price_value / total_position_value)
        if total_position_value > 0
        else Decimal(0)
    )
    significant_missing_prices = (
        bool(missing_price_symbols)
        and missing_share >= MISSING_PRICE_VALUE_SHARE_THRESHOLD
    )

    ytd_trusted = True
    if ytd.get("available"):
        start_method = ytd.get("start_method", "")
        current_method = ytd.get("current_method", valuation_method)
        if significant_missing_prices and current_method != "market":
            ytd_trusted = False
        elif start_method == "peildatum_snapshot" and current_method == "cost_basis":
            ytd_trusted = False

    problem_buys: list[str] = []
    for tx in portfolio.transactions.filter(transaction_type=TransactionType.BUY).select_related(
        "asset"
    )[:500]:
        if tx.quantity <= 0:
            continue
        if transaction_buy_cash_outflow(tx) <= 0:
            problem_buys.append(tx.asset.symbol)

    invested_trusted = not problem_buys
    if problem_buys:
        sample = ", ".join(sorted(set(problem_buys))[:5])
        warnings.append(
            f"Sommige aankopen missen een bedrag ({sample}). "
            "Importeer opnieuw of neem contact op met support."
        )

    return {
        "invested_trusted": invested_trusted,
        "ytd_trusted": ytd_trusted if ytd.get("available") else True,
        "warnings": _dedupe_warnings(warnings),
        "missing_price_symbols": missing_price_symbols[:20],
        "has_warnings": bool(warnings),
    }


def _dedupe_warnings(warnings: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for w in warnings:
        if w in seen:
            continue
        seen.add(w)
        out.append(w)
    return out
