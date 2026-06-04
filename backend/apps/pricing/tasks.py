import logging

from celery import shared_task

from apps.pricing.services.price_refresh import refresh_all_live_prices

logger = logging.getLogger(__name__)


@shared_task
def resolve_unmapped_instruments():
    from apps.pricing.services.instrument_service import resolve_unmapped_portfolio_isins

    report = resolve_unmapped_portfolio_isins(max_calls=50)
    logger.info("Instrument resolve: %s", report)
    return {"resolved": report.resolved, "failed": report.failed}


@shared_task
def refresh_live_prices():
    """
    Warm live-koerscache voor alle portefeuilleposities (elke 5 min via beat).
    Dashboard leest cache → snelle response, beperkte externe API-calls.
    """
    result = refresh_all_live_prices(force=True)
    logger.info("Live koersen ververst: %s", result)
    return result
