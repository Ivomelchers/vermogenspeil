"""Welke symbolen live verversen (alle actieve posities)."""

from apps.portfolio.models import AssetType, Position


def collect_live_price_items() -> list[tuple[str, str]]:
    """Unieke (symbol, asset_type) voor posities met quantity > 0."""
    items: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for position in Position.objects.filter(quantity__gt=0).select_related("asset"):
        asset = position.asset
        if asset.asset_type == AssetType.CASH:
            continue
        key = (asset.symbol.upper().strip(), asset.asset_type)
        if key in seen:
            continue
        seen.add(key)
        items.append(key)

    return items
