from django.test import SimpleTestCase

from apps.pricing.instrument_resolver import (
    list_unmapped_isins,
    looks_like_isin,
    resolve_yahoo_ticker,
)


class InstrumentResolverTests(SimpleTestCase):
    def test_isin_from_json_map(self):
        self.assertEqual(resolve_yahoo_ticker("IE00B4L5Y983"), "IWDA.AS")

    def test_symbol_alias(self):
        self.assertEqual(resolve_yahoo_ticker("ASML"), "ASML.AS")

    def test_unknown_isin_returns_isin(self):
        self.assertEqual(resolve_yahoo_ticker("XX0000000000"), "XX0000000000")

    def test_list_unmapped_isins(self):
        self.assertIn("XX0000000000", list_unmapped_isins(["XX0000000000", "IE00B4L5Y983"]))

    def test_looks_like_isin(self):
        self.assertTrue(looks_like_isin("IE00B4L5Y983"))
        self.assertFalse(looks_like_isin("BTC"))
