from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.portfolio.models import AssetType
from apps.pricing.instrument_resolver import resolve_yahoo_ticker
from apps.pricing.services import get_price_service


def _market_label(yahoo_ticker: str) -> str:
    upper = yahoo_ticker.upper()
    if upper.endswith(".AS"):
        return f"Euronext Amsterdam ({upper})"
    if upper.endswith(".L"):
        return f"LSE ({upper})"
    if upper.endswith(".DE"):
        return f"XETRA ({upper})"
    return upper


class LiveQuotesView(APIView):
    """Live koersen voor symbolen (gecachet)."""

    def get(self, request):
        symbols_raw = request.query_params.get("symbols", "")
        asset_type = request.query_params.get("asset_type", AssetType.CRYPTO)
        symbols = [s.strip().upper() for s in symbols_raw.split(",") if s.strip()]

        if not symbols:
            return Response(
                {
                    "data": None,
                    "error": "symbols_required",
                    "message": "Geef symbols op, bv. ?symbols=BTC,ETH&asset_type=crypto",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        service = get_price_service()
        quotes = service.get_live_prices([(symbol, asset_type) for symbol in symbols])

        payload = []
        for symbol in symbols:
            if symbol not in quotes:
                continue
            quote = quotes[symbol]
            market_ticker = resolve_yahoo_ticker(symbol) if quote.source == "yahoo" else symbol
            payload.append(
                {
                    "symbol": symbol,
                    "asset_type": asset_type,
                    "price_eur": str(quote.price_eur),
                    "source": quote.source,
                    "fetched_at": quote.fetched_at,
                    "from_cache": quote.from_cache,
                    "market_ticker": market_ticker,
                    "market_label": _market_label(market_ticker)
                    if quote.source == "yahoo"
                    else market_ticker,
                }
            )

        return Response(
            {
                "data": {"quotes": payload},
                "error": None,
                "message": f"{len(payload)} koers(en) opgehaald",
            }
        )
