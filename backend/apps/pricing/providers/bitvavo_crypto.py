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
    """Publieke Bitvavo ticker — geen API-key nodig."""

    asset_types = CRYPTO_ASSET_TYPES

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        self.base_url = (base_url or settings.BITVAVO_API_URL).rstrip("/")
        self.timeout = timeout

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        if not symbols:
            return {}

        markets = [f"{symbol.upper()}-EUR" for symbol in symbols]
        url = f"{self.base_url}/ticker/price"
        params = {"market": ",".join(markets)}

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("Bitvavo ticker ophalen mislukt: %s", exc)
            raise PriceFetchError("Bitvavo ticker niet beschikbaar") from exc

        if isinstance(payload, dict):
            payload = [payload]
        if not isinstance(payload, list):
            raise PriceFetchError("Onverwacht Bitvavo-antwoord")

        quotes: dict[str, LivePriceQuote] = {}
        for row in payload:
            market = row.get("market", "")
            price_raw = row.get("price")
            if not market.endswith("-EUR") or price_raw is None:
                continue
            symbol = market.removesuffix("-EUR")
            try:
                price_eur = Decimal(str(price_raw))
            except (InvalidOperation, TypeError):
                continue
            if price_eur <= 0:
                continue
            quotes[symbol] = LivePriceQuote(
                symbol=symbol,
                price_eur=price_eur,
                source="bitvavo",
            )

        return quotes
