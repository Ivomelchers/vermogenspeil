from django.test import Client, TestCase


class HealthCheckTests(TestCase):
    def test_health_returns_ok(self):
        response = Client().get("/api/v1/health/")

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["data"]["status"], "ok")
        self.assertIsNone(data["error"])
