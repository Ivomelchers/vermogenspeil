from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class LivePriceQuote:
    symbol: str
    price_eur: Decimal
    source: str


class LivePriceProvider(Protocol):
    asset_types: frozenset[str]

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        """Haal actuele EUR-prijzen op voor de gegeven symbolen."""

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types


class HistoricalPriceProvider(Protocol):
    def fetch_historical_price_eur(
        self,
        symbol: str,
        asset_type: str,
        on_date: date,
    ) -> Decimal | None:
        """Historische koers op een kalenderdag (UTC-datum)."""
