import pytest
from pathlib import Path
from apps.integrations.registry import PlatformFixtureRegistry


class TestPlatformFixtureRegistry:
    def test_discover_all_platforms(self):
        """Registry discovers all platforms with metadata and schema."""
        platforms = PlatformFixtureRegistry.get_all_platforms()

        # Should find at least trading212
        assert 'trading212' in platforms
        assert 'trade_republic' in platforms

        # Each platform has required keys
        for slug, platform_info in platforms.items():
            assert 'metadata' in platform_info
            assert 'schema' in platform_info
            assert 'fixtures_dir' in platform_info

    def test_platform_metadata_structure(self):
        """Metadata has required fields."""
        platforms = PlatformFixtureRegistry.get_all_platforms()
        trading212 = platforms['trading212']['metadata']

        assert trading212['name'] == 'Trading 212'
        assert trading212['slug'] == 'trading212'
        assert 'api_base_url' in trading212
        assert 'endpoints' in trading212
        assert isinstance(trading212['endpoints'], list)

    def test_get_fixtures_for_endpoint(self):
        """Get all fixture files for a specific endpoint."""
        fixtures = PlatformFixtureRegistry.get_fixtures_for_platform('trading212', 'positions')

        assert len(fixtures) > 0
        assert all(f.suffix == '.json' for f in fixtures)

    def test_validate_all_fixtures(self):
        """Validate all fixtures against their schemas."""
        errors = PlatformFixtureRegistry.validate_all_fixtures()

        # Should have no validation errors
        assert len(errors) == 0, f"Fixture validation failed: {errors}"
