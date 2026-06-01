from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.portfolio.models import AssetType
from apps.pricing.services import get_price_service


class LiveQuotesView(APIView):
    """Debug/Postman: live koersen voor symbolen (gecachet)."""

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

        payload = [
            {
                "symbol": symbol,
                "asset_type": asset_type,
                "price_eur": str(quotes[symbol].price_eur),
                "source": quotes[symbol].source,
                "fetched_at": quotes[symbol].fetched_at,
                "from_cache": quotes[symbol].from_cache,
            }
            for symbol in symbols
            if symbol in quotes
        ]

        return Response(
            {
                "data": {"quotes": payload},
                "error": None,
                "message": f"{len(payload)} koers(en) opgehaald",
            }
        )
