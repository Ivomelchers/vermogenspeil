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


@shared_task(bind=True, max_retries=3)
def refresh_symbol_cache(self):
    """
    Refresh symbol cache from all price providers (daily @ 2 AM).

    Discovers new symbols: meme coins, new listings, etc.
    Cache updated every 24h so new symbols are supported automatically.

    Rate limiting strategy:
    - Runs once per day (1 API call per provider per day)
    - Uses distributed lock to prevent concurrent calls
    - Exponential backoff on 429 (too many requests)
    - Falls back to cache if APIs unavailable
    """
    try:
        from apps.pricing.services.symbol_discovery import get_symbol_discovery_service

        service = get_symbol_discovery_service()
        results = service.refresh_all()

        status = results.get("status", "unknown")

        if status == "skipped_lock":
            logger.warning(
                "Symbol refresh skipped: already running (distributed lock). "
                "Retrying in 30 seconds."
            )
            raise self.retry(exc=None, countdown=30)

        elif status == "success":
            logger.info(
                "Symbol cache refreshed: %d crypto, %d stocks",
                results["crypto_total"],
                results["stocks_total"],
            )
            return results

        else:
            logger.warning("Symbol refresh completed with unknown status")
            return results

    except Exception as exc:
        # Only retry on network errors, not on application errors
        if self.request.retries < self.max_retries:
            countdown = 300 * (self.request.retries + 1)  # 5min, 10min, 15min
            logger.warning(
                "Symbol refresh failed. Retrying in %ds (attempt %d/%d)",
                countdown,
                self.request.retries + 1,
                self.max_retries,
            )
            raise self.retry(exc=exc, countdown=countdown)
        else:
            logger.exception(
                "Symbol refresh failed after %d retries. "
                "Falling back to cache.",
                self.max_retries,
            )
            return {"status": "failed", "retries": self.max_retries}
