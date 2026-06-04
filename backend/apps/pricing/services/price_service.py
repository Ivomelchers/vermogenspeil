import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers import (
    BitvavoCryptoProvider,
    CoinGeckoCryptoProvider,
    YahooEquitiesProvider,
)
from apps.pricing.providers.base import LivePriceProvider, LivePriceQuote
from apps.pricing.services.cache_keys import historical_price_cache_key, live_price_cache_key

logger = logging.getLogger(__name__)

_price_service: "PriceService | None" = None


@dataclass(frozen=True)
class PriceQuote:
    symbol: str
    asset_type: str
    price_eur: Decimal
    source: str
    fetched_at: str
    from_cache: bool


class PriceService:
    """Centrale koerslaag met Redis/locmem-cache en fallback per asset-type."""

    def __init__(self, providers: list[LivePriceProvider] | None = None):
        self.providers = providers or default_live_price_providers()

    def get_live_price_eur(self, symbol: str, asset_type: str) -> PriceQuote | None:
        quotes = self.get_live_prices([(symbol, asset_type)])
        return quotes.get(symbol.upper())

    def get_live_prices(
        self,
        items: list[tuple[str, str]],
        *,
        force_refresh: bool = False,
    ) -> dict[str, PriceQuote]:
        if not items:
            return {}

        normalized = [(symbol.upper().strip(), asset_type) for symbol, asset_type in items]
        result: dict[str, PriceQuote] = {}
        to_fetch: list[tuple[str, str]] = []

        for symbol, asset_type in normalized:
            cache_key = live_price_cache_key(symbol, asset_type)
            cached = None if force_refresh else cache.get(cache_key)
            if cached is not None:
                result[symbol] = PriceQuote(
                    symbol=symbol,
                    asset_type=asset_type,
                    price_eur=Decimal(str(cached["price_eur"])),
                    source=cached["source"],
                    fetched_at=cached["fetched_at"],
                    from_cache=True,
                )
                continue
            to_fetch.append((symbol, asset_type))

        if not to_fetch:
            return result

        fetched = self._fetch_from_providers(to_fetch)
        now_iso = timezone.now().isoformat()
        ttl = getattr(settings, "PRICE_CACHE_TTL_LIVE_SECONDS", 900)

        for symbol, asset_type in to_fetch:
            quote = fetched.get(symbol)
            if quote is None:
                continue
            cache_key = live_price_cache_key(symbol, asset_type)
            cache.set(
                cache_key,
                {
                    "price_eur": str(quote.price_eur),
                    "source": quote.source,
                    "fetched_at": now_iso,
                },
                timeout=ttl,
            )
            result[symbol] = PriceQuote(
                symbol=symbol,
                asset_type=asset_type,
                price_eur=quote.price_eur,
                source=quote.source,
                fetched_at=now_iso,
                from_cache=False,
            )

        return result

    def get_historical_price_eur(
        self,
        symbol: str,
        asset_type: str,
        on_date: date,
    ) -> Decimal | None:
        from apps.pricing.services.historical import fetch_historical_price_eur

        return fetch_historical_price_eur(symbol, asset_type, on_date)

    def _fetch_from_providers(
        self,
        items: list[tuple[str, str]],
    ) -> dict[str, LivePriceQuote]:
        """Per asset-type: probeer providers op volgorde tot elk symbool een koers heeft."""
        by_type: dict[str, list[str]] = {}
        for symbol, asset_type in items:
            by_type.setdefault(asset_type, []).append(symbol)

        merged: dict[str, LivePriceQuote] = {}
        for asset_type, symbols in by_type.items():
            providers = self._providers_for(asset_type)
            if not providers:
                continue
            pending = list(dict.fromkeys(s.upper() for s in symbols))
            for provider in providers:
                if not pending:
                    break
                try:
                    quotes = provider.fetch_live_prices(pending)
                except PriceFetchError as exc:
                    logger.warning(
                        "Koersprovider %s mislukt (%s): %s",
                        provider.__class__.__name__,
                        asset_type,
                        exc,
                    )
                    continue
                merged.update(quotes)
                pending = [s for s in pending if s not in quotes]

        return merged

    def _providers_for(self, asset_type: str) -> list[LivePriceProvider]:
        return [p for p in self.providers if p.supports_asset_type(asset_type)]


def default_live_price_providers() -> list[LivePriceProvider]:
    """
    Gratis stack (beste beschikbaar zonder betaalde feed):
    - Crypto: Bitvavo publiek → CoinGecko (batch, optioneel Demo-key)
    - ETF/aandelen/fondsen: Yahoo Finance (yfinance)
    """
    return [
        BitvavoCryptoProvider(),
        CoinGeckoCryptoProvider(),
        YahooEquitiesProvider(),
    ]


def get_price_service() -> PriceService:
    global _price_service
    if _price_service is None:
        _price_service = PriceService()
    return _price_service


def reset_price_service() -> None:
    """Alleen voor tests."""
    global _price_service
    _price_service = None
