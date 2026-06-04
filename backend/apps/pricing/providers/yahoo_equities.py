import logging
from decimal import Decimal, InvalidOperation

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.instrument_resolver import resolve_yahoo_ticker
from apps.pricing.providers.base import LivePriceQuote

logger = logging.getLogger(__name__)

EQUITY_ASSET_TYPES = frozenset(
    {
        AssetType.STOCK,
        AssetType.ETF,
        AssetType.FUND,
    }
)


class YahooEquitiesProvider:
    """Aandelen/ETF via Yahoo Finance (yfinance)."""

    asset_types = EQUITY_ASSET_TYPES

    def supports_asset_type(self, asset_type: str) -> bool:
        return asset_type in self.asset_types

    def fetch_live_prices(self, symbols: list[str]) -> dict[str, LivePriceQuote]:
        if not symbols:
            return {}

        try:
            import yfinance as yf
        except ImportError as exc:
            raise PriceFetchError("yfinance niet geïnstalleerd") from exc

        ticker_map = {symbol.upper(): resolve_yahoo_ticker(symbol) for symbol in symbols}
        yahoo_symbols = list(dict.fromkeys(ticker_map.values()))

        from apps.pricing.yfinance_utils import suppress_yfinance_noise

        try:
            with suppress_yfinance_noise():
                tickers = yf.Tickers(" ".join(yahoo_symbols))
        except Exception as exc:
            logger.warning("Yahoo Finance tickers laden mislukt: %s", exc)
            raise PriceFetchError("Yahoo Finance niet beschikbaar") from exc

        quotes: dict[str, LivePriceQuote] = {}

        for portfolio_symbol, yahoo_symbol in ticker_map.items():
            try:
                ticker = tickers.tickers.get(yahoo_symbol)
                if ticker is None:
                    continue
                info = ticker.fast_info
                price = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
                currency = (getattr(info, "currency", None) or "EUR").upper()
            except Exception as exc:
                logger.debug("Koers ophalen mislukt voor %s: %s", yahoo_symbol, exc)
                continue

            if price is None:
                continue

            try:
                price_decimal = Decimal(str(price))
            except (InvalidOperation, TypeError):
                continue

            if price_decimal <= 0:
                continue

            if currency != "EUR":
                logger.debug("Niet-EUR koers overgeslagen voor %s (%s)", yahoo_symbol, currency)
                continue

            quotes[portfolio_symbol] = LivePriceQuote(
                symbol=portfolio_symbol,
                price_eur=price_decimal,
                source="yahoo",
            )

        return quotes
