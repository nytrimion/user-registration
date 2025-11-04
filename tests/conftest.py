"""
Shared pytest fixtures for all tests.

This module provides reusable test fixtures for:
- FastAPI test client
- Database connection and cleanup
- Test data factories
- Repository access for integration tests
"""

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient

from src.account.domain.repositories.account_activation_repository import (
    AccountActivationRepository,
)
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.infrastructure.persistence.postgres_account_activation_repository import (
    PostgresAccountActivationRepository,
)
from src.account.infrastructure.persistence.postgres_account_repository import (
    PostgresAccountRepository,
)
from src.main import app
from src.shared.infrastructure.database.connection import PostgresConnectionFactory


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


@pytest.fixture
def account_repository() -> AccountRepository:
    """
    Fixture providing AccountRepository for integration tests.

    Returns:
        AccountRepository: PostgreSQL implementation for account persistence

    Usage:
        Used to query account data created via HTTP endpoints or set up
        test data that requires direct database access.

    Example:
        def test_something(client: TestClient, account_repository: AccountRepository):
            # Create account via HTTP
            response = client.post("/accounts", json={...})

            # Query account from database
            account = account_repository.find_by_email(Email("test@example.com"))
            assert account is not None
    """
    db = PostgresConnectionFactory()
    return PostgresAccountRepository(db)


@pytest.fixture
def account_activation_repository() -> AccountActivationRepository:
    """
    Fixture providing AccountActivationRepository for integration tests.

    Returns:
        AccountActivationRepository: PostgreSQL implementation for activation code persistence

    Usage:
        Used to retrieve activation codes generated during account creation.
        Essential for testing activation workflow end-to-end.

    Example:
        def test_activation(
            client: TestClient,
            account_repository: AccountRepository,
            account_activation_repository: AccountActivationRepository
        ):
            # Create account via HTTP
            response = client.post("/accounts", json={...})

            # Get account ID from database
            account = account_repository.find_by_email(Email("test@example.com"))

            # Get activation code from database
            activation = account_activation_repository.find_by_account_id(account.id)

            # Use code to activate account
            client.post(f"/accounts/{account.id}/activate", json={"code": activation.code.code})
    """
    db = PostgresConnectionFactory()
    return PostgresAccountActivationRepository(db)
