import hashlib
import hmac

from django.test import SimpleTestCase

from apps.integrations.bitvavo.client import BitvavoClient


class BitvavoClientSigningTests(SimpleTestCase):
    def test_sign_balance_matches_official_sdk_format(self):
        client = BitvavoClient("test-key", "test-secret")
        timestamp = 1548172481125
        signing_path = BitvavoClient.build_signing_path("balance")
        self.assertEqual(signing_path, "/v2/balance")

        expected_payload = f"{timestamp}GET/v2/balance"
        expected_sig = hmac.new(
            b"test-secret",
            expected_payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        self.assertEqual(client._sign(timestamp, "GET", signing_path), expected_sig)

    def test_sign_history_includes_query_string(self):
        client = BitvavoClient("test-key", "test-secret")
        timestamp = 1700000000000
        signing_path = BitvavoClient.build_signing_path(
            "account/history",
            "?page=1&maxItems=100",
        )
        self.assertEqual(signing_path, "/v2/account/history?page=1&maxItems=100")

        sig = client._sign(timestamp, "GET", signing_path)
        expected = hmac.new(
            b"test-secret",
            f"{timestamp}GET{signing_path}".encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        self.assertEqual(sig, expected)

    def test_strips_whitespace_from_credentials(self):
        client = BitvavoClient("  key  ", "  secret  ")
        self.assertEqual(client.api_key, "key")
        self.assertEqual(client.api_secret, "secret")
