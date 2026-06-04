from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from apps.pricing.openfigi_client import fetch_isin_match


class OpenFigiClientTests(SimpleTestCase):
    @override_settings(OPENFIGI_ENABLED=True)
    @patch("apps.pricing.openfigi_client.requests.post")
    def test_fetch_isin_match(self, mock_post):
        mock_post.return_value.ok = True
        mock_post.return_value.raise_for_status = lambda: None
        mock_post.return_value.json.return_value = [
            {
                "data": [
                    {
                        "ticker": "IWDA",
                        "exchCode": "AS",
                        "mic": "XAMS",
                        "marketSector": "Equity",
                        "securityType": "ETF",
                    }
                ]
            }
        ]
        match = fetch_isin_match("IE00B4L5Y983")
        self.assertIsNotNone(match)
        assert match is not None
        self.assertEqual(match.yahoo_ticker, "IWDA.AS")
