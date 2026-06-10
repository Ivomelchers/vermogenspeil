# backend/apps/integrations/tests/conftest.py

import pytest
import time
from apps.integrations.mock_server import MockApiServer

@pytest.fixture(scope="session")
def mock_api_server():
    """
    Start mock API server for the test session.

    Runs once per test session on port 5555.
    All tests can use this to make HTTP requests to mock APIs.
    """
    server = MockApiServer(port=5555)

    import threading
    thread = threading.Thread(target=server.start, daemon=True)
    thread.start()
    time.sleep(0.5)  # Wait for server to start

    yield server

    # Server cleanup happens when thread daemon exits

@pytest.fixture
def mock_api_url():
    """Base URL for mock API server."""
    return "http://localhost:5555/mock"
