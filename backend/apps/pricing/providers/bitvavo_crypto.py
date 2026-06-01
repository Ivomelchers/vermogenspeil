import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.base import LivePriceQuote

logger = logging.getLogger(__name__)

CRYPTO_ASSET_TYPES = frozenset({AssetType.CRYPTO})


class BitvavoCryptoProvider:
    """Publieke Bitvavo ticker — geen API-key nodig. Eén market per request."""

    asset_types = CRYPTO_ASSET_TYPES

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or settings.BITVAVO_API_URL).rstrip("/")
        self.timeout = timeout

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def _fetch_single_market(self, market: str) -> LivePriceQuote | None:
        url = f"{self.base_url}/ticker/price"
        try:
            response = requests.get(
                url,
                params={"market": market},
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Bitvavo ticker mislukt voor %s: %s", market, exc)
            return None

        if not isinstance(payload, dict):
            return None

        price_raw = payload.get("price")
        if price_raw is None:
            return None

        try:
            price_eur = Decimal(str(price_raw))
        except (InvalidOperation, TypeError):
            return None

        if price_eur <= 0:
            return None

        symbol = market.removesuffix("-EUR")
        return LivePriceQuote(symbol=symbol, price_eur=price_eur, source="bitvavo")

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        if not symbols:
            return {}

        quotes: dict[str, LivePriceQuote] = {}
        for symbol in symbols:
            market = f"{symbol.upper()}-EUR"
            quote = self._fetch_single_market(market)
            if quote:
                quotes[quote.symbol] = quote

        if not quotes:
            raise PriceFetchError("Bitvavo ticker niet beschikbaar")

        return quotes
