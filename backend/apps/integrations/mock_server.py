import json
import time
import threading
import logging
from pathlib import Path
from flask import Flask, jsonify, request

try:
    from apps.integrations.registry import PlatformFixtureRegistry
except ImportError:
    # Fallback for test environment imports
    from integrations.registry import PlatformFixtureRegistry

logger = logging.getLogger(__name__)


class MockApiServer:
    """Simulates all platform APIs using fixture data."""

    def __init__(self, port=5555):
        self.port = port
        self.app = Flask(__name__)
        self._register_routes()

    def _register_routes(self):
        """Dynamically register mock endpoints for all platforms."""
        platforms = PlatformFixtureRegistry.get_all_platforms()

        @self.app.route('/mock/<platform_slug>/<path:endpoint_path>', methods=['GET', 'POST'])
        def handle_request(platform_slug, endpoint_path):
            """Handle request to any platform endpoint."""

            if platform_slug not in platforms:
                return jsonify({"error": f"Platform {platform_slug} not found"}), 404

            # Normalize endpoint path (remove query params, split by /)
            endpoint_parts = endpoint_path.split('/')
            # First meaningful part after platform is the endpoint name
            endpoint_name = endpoint_parts[0] if endpoint_parts else 'unknown'

            # Get query param to select fixture (default: happy_path)
            fixture_name = request.args.get('fixture', 'happy_path')

            # Load fixture for this endpoint
            try:
                fixtures = PlatformFixtureRegistry.get_fixtures_for_platform(
                    platform_slug, endpoint_name
                )
            except (ValueError, KeyError):
                return jsonify({"error": f"No fixtures for {endpoint_name}"}), 404

            if not fixtures:
                return jsonify({"error": f"No fixtures for {endpoint_name}"}), 404

            # Find matching fixture
            fixture_path = None
            for f in fixtures:
                if fixture_name in f.stem:
                    fixture_path = f
                    break

            if not fixture_path:
                # Fall back to first fixture
                fixture_path = fixtures[0]

            # Load and return fixture data
            try:
                with open(fixture_path, 'r') as f:
                    response_data = json.load(f)
            except (OSError, json.JSONDecodeError) as e:
                logger.error(f"Error loading fixture {fixture_path}: {e}")
                return jsonify({"error": f"Error loading fixture"}), 500

            # Simulate latency
            time.sleep(0.1)

            return jsonify(response_data), 200

        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({"status": "ok"}), 200

    def start(self):
        """Start the Flask server (blocking)."""
        self.app.run(port=self.port, debug=False, use_reloader=False, threaded=True)

    @staticmethod
    def start_background(port=5555):
        """Start server in background thread."""
        server = MockApiServer(port=port)
        thread = threading.Thread(target=server.start, daemon=True)
        thread.start()
        time.sleep(0.5)
        return server
