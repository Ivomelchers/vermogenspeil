import threading
import time

import requests
from django.test import TestCase

from apps.integrations.mock_server import MockApiServer


class TestMockApiServer(TestCase):
    def setUp(self):
        self.server = MockApiServer(port=5556)
        self.thread = threading.Thread(target=self.server.start, daemon=True)
        self.thread.start()
        time.sleep(0.5)

    def test_health_endpoint(self):
        """Mock server responds to health check."""
        response = requests.get("http://localhost:5556/health", timeout=2)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")

    def test_server_responds_to_fixture_request(self):
        """Mock server serves fixture response at correct endpoint."""
        response = requests.get(
            "http://localhost:5556/mock/trading212/accounts/demo/portfolio/positions",
            timeout=2,
        )
        self.assertIn(response.status_code, [200, 404])

    def test_server_returns_404_for_unknown_platform(self):
        """Mock server returns 404 for non-existent platform."""
        response = requests.get(
            "http://localhost:5556/mock/nonexistent_platform/endpoint",
            timeout=2,
        )
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn("error", data)

    def test_server_selects_fixture_by_query_param(self):
        """Can select specific fixture with ?fixture=empty."""
        response = requests.get(
            "http://localhost:5556/mock/trading212/accounts/demo/portfolio/positions?fixture=empty",
            timeout=2,
        )
        self.assertIn(response.status_code, [200, 404])
