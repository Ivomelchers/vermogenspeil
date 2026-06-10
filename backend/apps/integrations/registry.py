import json
import yaml
from pathlib import Path
from typing import Dict, List, Tuple
from jsonschema import validate, ValidationError


class PlatformFixtureRegistry:
    """Discovers and manages all platform fixtures."""

    _FIXTURES_DIR = Path(__file__).parent / "tests" / "fixtures"

    @staticmethod
    def get_all_platforms() -> Dict[str, dict]:
        """
        Returns dict of all discovered platforms.

        Returns:
            {
                'trading212': {
                    'metadata': {...},
                    'schema': {...},
                    'fixtures_dir': Path(...)
                },
                ...
            }
        """
        platforms = {}

        for platform_dir in PlatformFixtureRegistry._FIXTURES_DIR.iterdir():
            if not platform_dir.is_dir():
                continue

            metadata_file = platform_dir / "metadata.yaml"
            schema_file = platform_dir / "schema.json"

            if not (metadata_file.exists() and schema_file.exists()):
                continue

            with open(metadata_file, 'r') as f:
                metadata = yaml.safe_load(f)

            with open(schema_file, 'r') as f:
                schema = json.load(f)

            platforms[metadata['slug']] = {
                'metadata': metadata,
                'schema': schema,
                'fixtures_dir': platform_dir,
            }

        return platforms

    @staticmethod
    def get_fixtures_for_platform(platform_slug: str, endpoint_name: str) -> List[Path]:
        """
        Get all fixture files for a platform endpoint.

        Args:
            platform_slug: e.g., 'trading212'
            endpoint_name: e.g., 'positions'

        Returns:
            List of Path objects matching {endpoint_name}_*.json
        """
        platforms = PlatformFixtureRegistry.get_all_platforms()

        if platform_slug not in platforms:
            raise ValueError(f"Platform {platform_slug} not found")

        fixtures_dir = platforms[platform_slug]['fixtures_dir'] / 'responses'

        if not fixtures_dir.exists():
            return []

        return sorted(fixtures_dir.glob(f"{endpoint_name}_*.json"))

    @staticmethod
    def validate_all_fixtures() -> List[Tuple[Path, ValidationError]]:
        """
        Validate all fixture files against their platform schemas.

        Returns:
            List of (fixture_path, error) tuples. Empty if all valid.
        """
        errors = []
        platforms = PlatformFixtureRegistry.get_all_platforms()

        for platform_slug, platform_info in platforms.items():
            schema = platform_info['schema']
            fixtures_dir = platform_info['fixtures_dir'] / 'responses'

            if not fixtures_dir.exists():
                continue

            for fixture_file in fixtures_dir.glob("*.json"):
                with open(fixture_file, 'r') as f:
                    fixture_data = json.load(f)

                # Determine schema definition to use
                endpoint = fixture_file.stem.split('_')[0]
                schema_key = f"{endpoint.title()}Response"
                schema_def = schema.get('definitions', {}).get(schema_key, schema)

                try:
                    validate(instance=fixture_data, schema=schema_def)
                except ValidationError as e:
                    errors.append((fixture_file, e))

        return errors
