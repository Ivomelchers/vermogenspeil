import json

from django.test import TestCase
from jsonschema import ValidationError, validate

from apps.integrations.registry import PlatformFixtureRegistry


class TestApiContract(TestCase):
    """Validates all fixture files against their platform schemas."""

    def test_validate_all_fixtures(self):
        """All fixtures must validate against their platform's schema."""
        errors = PlatformFixtureRegistry.validate_all_fixtures()

        if errors:
            error_msg = "\n".join(
                f"  {fixture_path}: {error.message}"
                for fixture_path, error in errors
            )
            self.fail(f"Fixture validation errors:\n{error_msg}")

    def test_platform_fixtures_valid(self):
        """Each platform's fixtures must be valid."""
        platforms = PlatformFixtureRegistry.get_all_platforms()

        if not platforms:
            self.skipTest("No platforms discovered yet")

        for platform_slug, platform in platforms.items():
            schema = platform["schema"]
            fixtures_dir = platform["fixtures_dir"] / "responses"

            if not fixtures_dir.exists():
                continue

            errors = []
            for fixture_file in fixtures_dir.glob("*.json"):
                with open(fixture_file, "r") as f:
                    fixture_data = json.load(f)

                endpoint = fixture_file.stem.split("_")[0]
                schema_key = f"{endpoint.title()}Response"
                schema_def = schema.get("definitions", {}).get(schema_key, schema)

                try:
                    validate(instance=fixture_data, schema=schema_def)
                except ValidationError as e:
                    errors.append((fixture_file.name, e.message))

            if errors:
                error_msg = "\n".join(f"  {name}: {msg}" for name, msg in errors)
                self.fail(f"Validation errors in {platform_slug}:\n{error_msg}")
