from decimal import Decimal
from unittest.mock import MagicMock, patch

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.portfolio.models import Asset, AssetType, Portfolio, Position, VermogensCategorie
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.base import LivePriceQuote
from apps.pricing.services.price_refresh import refresh_all_live_prices
from apps.pricing.services.price_service import PriceService, reset_price_service


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    },
    PRICE_CACHE_TTL_LIVE_SECONDS=300,
)
class PriceRefreshTests(TestCase):
    def setUp(self):
        cache.clear()
        reset_price_service()

    def tearDown(self):
        reset_price_service()
        cache.clear()

    @patch("apps.pricing.services.price_service.YahooEquitiesProvider")
    @patch("apps.pricing.services.price_service.CoinGeckoCryptoProvider")
    @patch("apps.pricing.services.price_service.BitvavoCryptoProvider")
    def test_crypto_fallback_to_coingecko(self, mock_bitvavo_cls, mock_cg_cls, mock_yahoo_cls):
        mock_bitvavo = MagicMock()
        mock_bitvavo.supports_asset_type.return_value = True
        mock_bitvavo.fetch_live_prices.side_effect = PriceFetchError("bitvavo down")
        mock_bitvavo_cls.return_value = mock_bitvavo

        mock_cg = MagicMock()
        mock_cg.supports_asset_type.return_value = True
        mock_cg.fetch_live_prices.return_value = {
            "ETH": LivePriceQuote(symbol="ETH", price_eur=Decimal("3000"), source="coingecko"),
        }
        mock_cg_cls.return_value = mock_cg

        mock_yahoo = MagicMock()
        mock_yahoo.supports_asset_type.return_value = False
        mock_yahoo_cls.return_value = mock_yahoo

        service = PriceService()
        quotes = service.get_live_prices([("ETH", AssetType.CRYPTO)], force_refresh=True)
        self.assertEqual(quotes["ETH"].source, "coingecko")

    def test_refresh_command_collects_positions(self):
        from django.contrib.auth import get_user_model

        user = get_user_model().objects.create_user(
            email="prices@example.com",
            password="SecurePass123!",
        )
        portfolio = Portfolio.objects.create(user=user, name="P", is_default=True)
        asset = Asset.objects.create(
            user=user,
            symbol="BTC",
            asset_type=AssetType.CRYPTO,
            category=VermogensCategorie.BELEGGING,
        )
        Position.objects.create(portfolio=portfolio, asset=asset, quantity=Decimal("1"))

        with patch(
            "apps.pricing.services.price_refresh.get_price_service"
        ) as mock_get:
            mock_get.return_value.get_live_prices.return_value = {
                "BTC": MagicMock(),
            }
            result = refresh_all_live_prices(force=True)
            self.assertEqual(result["symbols_requested"], 1)
            mock_get.return_value.get_live_prices.assert_called_once()
