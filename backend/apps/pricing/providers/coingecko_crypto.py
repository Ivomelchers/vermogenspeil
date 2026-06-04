"""CoinGecko live crypto (Demo API-key optioneel) — fallback na Bitvavo."""

import logging
from decimal import Decimal, InvalidOperation

import requests
from django.conf import settings

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.base import LivePriceQuote

logger = logging.getLogger(__name__)

CRYPTO_ASSET_TYPES = frozenset({AssetType.CRYPTO})

# Uitbreidbaar; onbekende symbolen worden overgeslagen (Bitvavo/Yahoo dekken rest).
COINGECKO_COIN_IDS: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOT": "polkadot",
    "LINK": "chainlink",
    "LTC": "litecoin",
}


class CoinGeckoCryptoProvider:
    """Batch live EUR-prijs via CoinGecko simple/price (1 call voor meerdere coins)."""

    asset_types = CRYPTO_ASSET_TYPES

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.base_url = "https://api.coingecko.com/api/v3"

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def _headers(self) -> dict[str, str]:
        key = getattr(settings, "COINGECKO_API_KEY", "") or ""
        if key:
            return {"x-cg-demo-api-key": key}
        return {}

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        coin_map: dict[str, str] = {}
        for symbol in symbols:
            upper = symbol.upper().strip()
            coin_id = COINGECKO_COIN_IDS.get(upper)
            if coin_id and coin_id not in coin_map:
                coin_map[coin_id] = upper

        if not coin_map:
            return {}

        try:
            response = requests.get(
                f"{self.base_url}/simple/price",
                params={
                    "ids": ",".join(coin_map.keys()),
                    "vs_currencies": "eur",
                },
                headers=self._headers(),
                timeout=self.timeout,
            )
            response.raise_for_status()
            payload = response.json()
        except (requests.RequestException, ValueError) as exc:
            logger.warning("CoinGecko live prices mislukt: %s", exc)
            raise PriceFetchError("CoinGecko niet beschikbaar") from exc

        if not isinstance(payload, dict):
            return {}

        quotes: dict[str, LivePriceQuote] = {}
        for coin_id, portfolio_symbol in coin_map.items():
            entry = payload.get(coin_id)
            if not isinstance(entry, dict):
                continue
            eur = entry.get("eur")
            if eur is None:
                continue
            try:
                price = Decimal(str(eur))
            except (InvalidOperation, TypeError):
                continue
            if price <= 0:
                continue
            quotes[portfolio_symbol] = LivePriceQuote(
                symbol=portfolio_symbol,
                price_eur=price,
                source="coingecko",
            )

        if not quotes:
            raise PriceFetchError("CoinGecko: geen EUR-koersen in response")

        return quotes
