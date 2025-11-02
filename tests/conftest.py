"""
Shared pytest fixtures for all tests.

This module provides reusable test fixtures for:
- FastAPI test client
- Database connection and cleanup
- Test data factories
"""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client() -> Generator[TestClient, Any]:
    """
    Fixture providing a FastAPI test client.

    Yields:
        TestClient: Configured test client for API requests
    """
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def api_base_url() -> str:
    """
    Fixture providing the base URL for API endpoints.

    Returns:
        str: Base URL for the API
    """
    return "http://testserver"
