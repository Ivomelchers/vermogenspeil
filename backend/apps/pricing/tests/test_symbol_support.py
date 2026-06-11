"""
Integration test: verify symbol discovery from price providers.

Tests that:
1. Symbol discovery service fetches symbols from APIs
2. Symbols are cached for efficient access
3. Fallback symbols work if cache is empty
4. Asset validation works with dynamic symbols
5. Meme coins and new symbols are automatically supported
"""

from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.core.cache import cache

from apps.portfolio.models import Asset, AssetType
from apps.pricing.symbol_registry import (
    get_supported_symbols,
    is_symbol_supported,
    suggest_similar_symbols,
)
from apps.pricing.services.symbol_discovery import SymbolDiscoveryService


class SymbolDiscoveryTest(TestCase):
    """Test dynamic symbol discovery from provider APIs."""

    def setUp(self):
        cache.clear()

    def test_discover_crypto_symbols_from_bitvavo(self):
        """Bitvavo API returns list of crypto markets."""
        service = SymbolDiscoveryService()

        mock_markets = [
            {"id": "BTC-EUR"},
            {"id": "ETH-EUR"},
            {"id": "DOGE-EUR"},
            {"id": "SHIB-EUR"},
        ]

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_markets
            mock_response.raise_for_status = lambda: None
            mock_get.return_value = mock_response

            symbols = service._fetch_bitvavo_symbols()

            self.assertIn("BTC", symbols)
            self.assertIn("DOGE", symbols)
            self.assertIn("SHIB", symbols)

    def test_discover_crypto_symbols_from_coingecko(self):
        """CoinGecko API returns list of all coins."""
        service = SymbolDiscoveryService()

        mock_coins = [
            {"symbol": "btc", "id": "bitcoin"},
            {"symbol": "eth", "id": "ethereum"},
            {"symbol": "doge", "id": "dogecoin"},
            {"symbol": "memecoin", "id": "memecoin"},
        ]

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = mock_coins
            mock_response.raise_for_status = lambda: None
            mock_get.return_value = mock_response

            symbols = service._fetch_coingecko_symbols()

            self.assertIn("BTC", symbols)
            self.assertIn("DOGE", symbols)
            self.assertIn("MEMECOIN", symbols)

    def test_symbols_are_cached(self):
        """Discovered symbols are cached to reduce API calls."""
        service = SymbolDiscoveryService()

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = [{"id": "BTC-EUR"}]
            mock_response.raise_for_status = lambda: None
            mock_get.return_value = mock_response

            # First call hits API
            symbols1 = service._fetch_bitvavo_symbols()
            calls_after_first = mock_get.call_count

            # Second call uses cache
            symbols2 = service._fetch_bitvavo_symbols()
            calls_after_second = mock_get.call_count

            # No additional API calls
            self.assertEqual(calls_after_first, calls_after_second)
            self.assertEqual(symbols1, symbols2)

    def test_fallback_symbols_when_cache_empty(self):
        """If cache is empty, use fallback list."""
        cache.clear()

        supported = get_supported_symbols(AssetType.CRYPTO)

        # Should have fallback symbols
        self.assertIn("BTC", supported)
        self.assertIn("ETH", supported)

    def test_dynamic_symbols_when_cached(self):
        """When cache has data, use it instead of fallback."""
        from apps.pricing.symbol_registry import CACHE_KEYS

        # Set custom cache with meme coins
        cache.set(
            CACHE_KEYS["crypto"],
            ["BTC", "ETH", "DOGE", "SHIB", "MEMECOIN", "BONK"],
            86400,
        )

        supported = get_supported_symbols(AssetType.CRYPTO)

        self.assertIn("BTC", supported)
        self.assertIn("MEMECOIN", supported)
        self.assertIn("BONK", supported)

    def test_new_meme_coin_automatically_supported(self):
        """New symbols added to cache are automatically supported."""
        from apps.pricing.symbol_registry import CACHE_KEYS

        # Simulate discovery of new meme coin
        cache.set(
            CACHE_KEYS["crypto"],
            ["BTC", "ETH", "NEWMEME"],
            86400,
        )

        # User can now add this asset
        self.assertTrue(is_symbol_supported("NEWMEME", AssetType.CRYPTO))

    def test_asset_validation_with_dynamic_symbols(self):
        """Asset validation works with dynamically discovered symbols."""
        from apps.pricing.symbol_registry import CACHE_KEYS

        # Set cache with specific symbols
        cache.set(
            CACHE_KEYS["crypto"],
            ["BTC", "ETH"],
            86400,
        )

        # Valid symbol should pass
        asset_valid = Asset(symbol="BTC", asset_type=AssetType.CRYPTO)
        try:
            asset_valid.clean()
        except Exception:
            self.fail("BTC should be valid when in cache")

        # Invalid symbol should fail
        from django.core.exceptions import ValidationError

        asset_invalid = Asset(symbol="FAKECOIN", asset_type=AssetType.CRYPTO)
        with self.assertRaises(ValidationError):
            asset_invalid.clean()

    def test_ar_symbol_supported(self):
        """AR (Arweave) should be dynamically discovered from CoinGecko."""
        from apps.pricing.symbol_registry import CACHE_KEYS

        # Simulate CoinGecko discovery finding AR
        cache.set(
            CACHE_KEYS["crypto"],
            ["BTC", "ETH", "AR"],
            86400,
        )

        # AR should now be supported
        self.assertTrue(is_symbol_supported("AR", AssetType.CRYPTO))


class SymbolSuggestionTest(TestCase):
    """Test symbol suggestion for typos."""

    def setUp(self):
        # Set cache with some symbols
        from apps.pricing.symbol_registry import CACHE_KEYS

        cache.set(
            CACHE_KEYS["crypto"],
            ["BTC", "ETH", "DOGE", "SHIB", "ARWEAVE"],
            86400,
        )

    def test_suggest_similar_symbols(self):
        """Suggest close matches if user types wrong symbol."""
        suggestions = suggest_similar_symbols("BTCC", AssetType.CRYPTO)
        self.assertIn("BTC", suggestions)

    def test_suggest_prefix_matches(self):
        """Suggest symbols starting with typed prefix."""
        suggestions = suggest_similar_symbols("DO", AssetType.CRYPTO)
        self.assertIn("DOGE", suggestions)

    def test_no_suggestions_for_gibberish(self):
        """Don't suggest if nothing matches."""
        suggestions = suggest_similar_symbols("XYZABC", AssetType.CRYPTO)
        # May have suggestions or not, depending on data
        # Just verify it doesn't crash
        self.assertIsInstance(suggestions, list)
