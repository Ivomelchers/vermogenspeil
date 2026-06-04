"""Geforceerde refresh van live koersen (Celery / management command)."""

from django.utils import timezone

from apps.pricing.services.price_service import get_price_service
from apps.pricing.services.symbol_registry import collect_live_price_items


def refresh_all_live_prices(*, force: bool = True) -> dict:
    from apps.pricing.services.instrument_service import resolve_unmapped_portfolio_isins

    resolve_unmapped_portfolio_isins(max_calls=25)

    items = collect_live_price_items()
    if not items:
        return {"symbols_requested": 0, "symbols_priced": 0, "as_of": timezone.now().isoformat()}

    quotes = get_price_service().get_live_prices(items, force_refresh=force)
    return {
        "symbols_requested": len(items),
        "symbols_priced": len(quotes),
        "as_of": timezone.now().isoformat(),
    }
