from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.portfolio.models import AssetType
from apps.pricing.providers.base import LivePriceQuote
from apps.pricing.services.price_service import PriceService, reset_price_service


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    },
    PRICE_CACHE_TTL_LIVE_SECONDS=900,
)
class PriceServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        reset_price_service()

    def tearDown(self):
        reset_price_service()
        cache.clear()

    def test_live_price_cached_on_second_request(self):
        mock_provider = MagicMock()
        mock_provider.asset_types = frozenset({AssetType.CRYPTO})
        mock_provider.supports_asset_type.return_value = True
        mock_provider.fetch_live_prices.return_value = {
            "BTC": LivePriceQuote(symbol="BTC", price_eur=Decimal("90000"), source="bitvavo"),
        }

        service = PriceService(providers=[mock_provider])

        first = service.get_live_prices([("BTC", AssetType.CRYPTO)])
        second = service.get_live_prices([("BTC", AssetType.CRYPTO)])

        self.assertFalse(first["BTC"].from_cache)
        self.assertTrue(second["BTC"].from_cache)
        mock_provider.fetch_live_prices.assert_called_once()

    @patch("apps.pricing.providers.bitvavo_crypto.requests.get")
    def test_bitvavo_provider_parses_single_market(self, mock_get):
        mock_get.return_value.json.return_value = {
            "market": "BTC-EUR",
            "price": "95000.12",
        }
        mock_get.return_value.raise_for_status = MagicMock()

        from apps.pricing.providers.bitvavo_crypto import BitvavoCryptoProvider

        quotes = BitvavoCryptoProvider(base_url="https://api.bitvavo.com/v2").fetch_live_prices(
            ["BTC"]
        )

        self.assertEqual(quotes["BTC"].price_eur, Decimal("95000.12"))
        self.assertEqual(quotes["BTC"].source, "bitvavo")

    @patch("apps.pricing.providers.bitvavo_crypto.requests.get")
    def test_bitvavo_provider_fetches_each_market_separately(self, mock_get):
        def fake_get(url, params=None, timeout=None):
            response = MagicMock()
            response.raise_for_status = MagicMock()
            market = (params or {}).get("market", "")
            prices = {"BTC-EUR": "90000", "ETH-EUR": "3500"}
            response.json.return_value = {"market": market, "price": prices.get(market, "0")}
            return response

        mock_get.side_effect = fake_get

        from apps.pricing.providers.bitvavo_crypto import BitvavoCryptoProvider

        quotes = BitvavoCryptoProvider(base_url="https://api.bitvavo.com/v2").fetch_live_prices(
            ["BTC", "ETH"]
        )

        self.assertEqual(mock_get.call_count, 2)
        self.assertEqual(len(quotes), 2)
        self.assertEqual(quotes["ETH"].price_eur, Decimal("3500"))
