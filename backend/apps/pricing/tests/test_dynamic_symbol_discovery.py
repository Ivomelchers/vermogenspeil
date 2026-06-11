"""Test dynamic symbol discovery for CoinGecko."""

from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.core.cache import cache
from django.test import TestCase, override_settings

from apps.portfolio.models import AssetType
from apps.pricing.exceptions import PriceFetchError
from apps.pricing.providers.coingecko_crypto import CoinGeckoCryptoProvider
from apps.pricing.services.price_service import PriceService, reset_price_service


@override_settings(
    CACHES={
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    },
)
class DynamicSymbolDiscoveryTests(TestCase):
    """Test that unknown coins (BRETT, CETUS, MANA, etc.) are dynamically resolved."""

    def setUp(self):
        cache.clear()
        reset_price_service()

    def tearDown(self):
        reset_price_service()
        cache.clear()

    @patch("apps.pricing.providers.coingecko_crypto.requests.get")
    def test_brett_symbol_discovery(self, mock_get):
        """Test that BRETT (unknown coin) is discovered dynamically."""
        provider = CoinGeckoCryptoProvider()

        # Mock search response for BRETT
        search_response = MagicMock()
        search_response.json.return_value = {
            "coins": [
                {"id": "brett", "symbol": "BRETT", "name": "Brett"},
            ]
        }

        # Mock price response for brett
        price_response = MagicMock()
        price_response.json.return_value = {
            "brett": {"eur": 0.0001},
        }

        # First call = search, second call = price
        mock_get.side_effect = [search_response, price_response]

        quotes = provider.fetch_live_prices(["BRETT"])

        # Should have found BRETT and fetched price
        self.assertIn("BRETT", quotes)
        self.assertEqual(quotes["BRETT"].price_eur, Decimal("0.0001"))
        self.assertEqual(quotes["BRETT"].source, "coingecko")

    @patch("apps.pricing.providers.coingecko_crypto.requests.get")
    def test_multiple_new_coins(self, mock_get):
        """Test that multiple unknown coins are resolved."""
        provider = CoinGeckoCryptoProvider()

        # Mock search responses
        search_response_cetus = MagicMock()
        search_response_cetus.json.return_value = {
            "coins": [{"id": "cetus", "symbol": "CETUS", "name": "Cetus Protocol"}]
        }

        search_response_mana = MagicMock()
        search_response_mana.json.return_value = {
            "coins": [{"id": "decentraland", "symbol": "MANA", "name": "Decentraland"}]
        }

        # Mock price response
        price_response = MagicMock()
        price_response.json.return_value = {
            "cetus": {"eur": 0.5},
            "decentraland": {"eur": 0.8},
        }

        mock_get.side_effect = [
            search_response_cetus,
            search_response_mana,
            price_response,
        ]

        quotes = provider.fetch_live_prices(["CETUS", "MANA"])

        self.assertIn("CETUS", quotes)
        self.assertIn("MANA", quotes)
        self.assertEqual(quotes["CETUS"].price_eur, Decimal("0.5"))
        self.assertEqual(quotes["MANA"].price_eur, Decimal("0.8"))

    @patch("apps.pricing.providers.coingecko_crypto.requests.get")
    def test_symbol_caching(self, mock_get):
        """Test that symbol→coin_id mappings are cached."""
        provider = CoinGeckoCryptoProvider()

        search_response = MagicMock()
        search_response.json.return_value = {
            "coins": [{"id": "brett", "symbol": "BRETT"}]
        }

        price_response = MagicMock()
        price_response.json.return_value = {
            "brett": {"eur": 0.0001},
        }

        # First call: search + price
        # Second call: just price (search is cached)
        mock_get.side_effect = [search_response, price_response, price_response]

        # First call
        quotes1 = provider.fetch_live_prices(["BRETT"])
        call_count_after_first = mock_get.call_count

        # Second call — should use cache, fewer API calls
        quotes2 = provider.fetch_live_prices(["BRETT"])
        call_count_after_second = mock_get.call_count

        # Second call should only make 1 new call (price only, no search)
        self.assertEqual(call_count_after_second - call_count_after_first, 1)
        self.assertEqual(quotes1["BRETT"].price_eur, quotes2["BRETT"].price_eur)

    @patch("apps.pricing.providers.coingecko_crypto.requests.get")
    def test_mixed_known_and_unknown_coins(self, mock_get):
        """Test that unknown coins like BRETT work (even known coins like BTC are searched)."""
        provider = CoinGeckoCryptoProvider()

        # Mock search for BTC
        search_btc = MagicMock()
        search_btc.json.return_value = {
            "coins": [{"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"}]
        }

        # Mock search for BRETT
        search_brett = MagicMock()
        search_brett.json.return_value = {
            "coins": [{"id": "brett", "symbol": "BRETT"}]
        }

        # Mock price response
        price_response = MagicMock()
        price_response.json.return_value = {
            "bitcoin": {"eur": 50000},
            "brett": {"eur": 0.0001},
        }

        mock_get.side_effect = [search_btc, search_brett, price_response]

        quotes = provider.fetch_live_prices(["BTC", "BRETT"])

        self.assertIn("BTC", quotes)
        self.assertIn("BRETT", quotes)
        self.assertEqual(quotes["BTC"].price_eur, Decimal("50000"))
        self.assertEqual(quotes["BRETT"].price_eur, Decimal("0.0001"))

    @patch("apps.pricing.providers.coingecko_crypto.requests.get")
    def test_unknown_symbol_marked_as_not_found(self, mock_get):
        """Test that symbols not found are cached to avoid repeated searches."""
        provider = CoinGeckoCryptoProvider()

        search_response = MagicMock()
        search_response.json.return_value = {"coins": []}  # Not found

        price_response = MagicMock()
        price_response.json.return_value = {}  # No prices

        # First call searches, second call uses cache without searching
        mock_get.side_effect = [search_response, price_response]

        quotes1 = provider.fetch_live_prices(["FAKECOIN"])
        self.assertEqual(len(quotes1), 0)

        # Second call — should not try to search again
        with patch("apps.pricing.providers.coingecko_crypto.requests.get") as mock_get2:
            quotes2 = provider.fetch_live_prices(["FAKECOIN"])
            # Should only call price endpoint, not search
            self.assertEqual(len(quotes2), 0)

    @patch("apps.pricing.providers.coingecko_crypto.requests.get")
    def test_tester_bitvavo_coins(self, mock_get):
        """
        Test ALL coins from tester's Bitvavo import:
        TIA, BRETT, MANA, AXS, CHZ, CETUS, ADA, SUI, SOL, TAO, NEAR, SAND
        """
        provider = CoinGeckoCryptoProvider()
        test_coins = ["TIA", "BRETT", "MANA", "AXS", "CHZ", "CETUS", "ADA", "SUI", "SOL", "TAO", "NEAR", "SAND"]

        # Mock search responses for all coins
        search_responses = {
            "TIA": {"id": "tia", "symbol": "TIA"},
            "BRETT": {"id": "brett", "symbol": "BRETT"},
            "MANA": {"id": "decentraland", "symbol": "MANA"},
            "AXS": {"id": "axie-infinity", "symbol": "AXS"},
            "CHZ": {"id": "chiliz", "symbol": "CHZ"},
            "CETUS": {"id": "cetus", "symbol": "CETUS"},
            "ADA": {"id": "cardano", "symbol": "ADA"},
            "SUI": {"id": "sui", "symbol": "SUI"},
            "SOL": {"id": "solana", "symbol": "SOL"},
            "TAO": {"id": "bittensor", "symbol": "TAO"},
            "NEAR": {"id": "near", "symbol": "NEAR"},
            "SAND": {"id": "the-sandbox", "symbol": "SAND"},
        }

        # Create mock responses for searches
        def mock_search(url, **kwargs):
            query = kwargs.get("params", {}).get("query", "").upper()
            response = MagicMock()
            if query in search_responses:
                response.json.return_value = {"coins": [search_responses[query]]}
            else:
                response.json.return_value = {"coins": []}
            return response

        # Create mock response for prices
        price_response = MagicMock()
        price_response.json.return_value = {
            "tia": {"eur": 5.50},
            "brett": {"eur": 0.0001},
            "decentraland": {"eur": 0.75},
            "axie-infinity": {"eur": 5.20},
            "chiliz": {"eur": 0.12},
            "cetus": {"eur": 0.55},
            "cardano": {"eur": 0.95},
            "sui": {"eur": 4.20},
            "solana": {"eur": 210.00},
            "bittensor": {"eur": 650.00},
            "near": {"eur": 8.40},
            "the-sandbox": {"eur": 0.65},
        }

        # All searches first, then one price call
        search_mocks = [mock_search(None, params={"query": coin}) for coin in test_coins]
        mock_get.side_effect = search_mocks + [price_response]

        # Fetch prices for all coins
        quotes = provider.fetch_live_prices(test_coins)

        # Verify all coins were recognized
        for coin in test_coins:
            self.assertIn(coin, quotes, f"{coin} should be in quotes")
            self.assertGreater(quotes[coin].price_eur, 0, f"{coin} should have non-zero price")
            self.assertEqual(quotes[coin].source, "coingecko")

        # Verify exact coin count
        self.assertEqual(len(quotes), len(test_coins))
