from django.test import TestCase

from apps.integrations.registry import PlatformFixtureRegistry


class TestPlatformFixtureRegistry(TestCase):
    def test_discover_all_platforms(self):
        """Registry discovers all platforms with metadata and schema."""
        platforms = PlatformFixtureRegistry.get_all_platforms()

        # Should find at least trading212
        self.assertIn("trading212", platforms)
        self.assertIn("trade_republic", platforms)

        # Each platform has required keys
        for slug, platform_info in platforms.items():
            self.assertIn("metadata", platform_info)
            self.assertIn("schema", platform_info)
            self.assertIn("fixtures_dir", platform_info)

    def test_platform_metadata_structure(self):
        """Metadata has required fields."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        trading212 = platforms["trading212"]["metadata"]

        self.assertEqual(trading212["name"], "Trading 212")
        self.assertEqual(trading212["slug"], "trading212")
        self.assertIn("api_base_url", trading212)
        self.assertIn("endpoints", trading212)
        self.assertIsInstance(trading212["endpoints"], list)

    def test_get_fixtures_for_endpoint(self):
        """Get all fixture files for a specific endpoint."""
        fixtures = PlatformFixtureRegistry.get_fixtures_for_platform("trading212", "portfolio")

        self.assertGreater(len(fixtures), 0)
        self.assertTrue(all(f.suffix == ".json" for f in fixtures))

    def test_validate_all_fixtures(self):
        """Validate all fixtures against their schemas."""
        errors = PlatformFixtureRegistry.validate_all_fixtures()

        self.assertEqual(len(errors), 0, f"Fixture validation failed: {errors}")
