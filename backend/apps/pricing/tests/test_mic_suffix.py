from django.test import SimpleTestCase

from apps.pricing.mic_suffix import build_yahoo_ticker


class MicSuffixTests(SimpleTestCase):
    def test_exch_code(self):
        self.assertEqual(build_yahoo_ticker(ticker="IWDA", exch_code="AS"), "IWDA.AS")
