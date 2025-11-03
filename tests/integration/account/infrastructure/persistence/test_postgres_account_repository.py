"""
Integration tests for PostgresAccountRepository.

These tests validate the repository behavior with a real PostgreSQL database.
They ensure proper create/find operations, constraint enforcement, and
entity round-trip preservation.

Test Strategy:
    - Real PostgreSQL database (Docker service)
    - Test CRUD operations (create, find_by_email)
    - Test constraint enforcement (UNIQUE email)
    - Test round-trip (entity → DB → entity preserves data)
    - Repository commits automatically (no manual commit needed)

Database:
    - Uses DATABASE_* environment variables (same as application)
    - Tests run against real PostgreSQL instance
    - Repository commits transactions automatically
    - Tests are independent (no shared state)

Fixtures:
    - repository: PostgresAccountRepository with real connection pool
    - test_email/test_password: Sample value objects for testing
"""

import pytest
from psycopg2 import IntegrityError

from src.account.domain.entities.account import Account
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.infrastructure.persistence.postgres_account_repository import (
    PostgresAccountRepository,
)
from src.shared.infrastructure.database.connection import PostgresConnectionFactory


@pytest.fixture
def repository() -> PostgresAccountRepository:
    """
    Provide PostgresAccountRepository with real connection pool.

    Creates a repository instance connected to the test database.
    Each test gets a fresh repository instance.

    Returns:
        PostgresAccountRepository: Repository with real PostgreSQL connection
    """
    db = PostgresConnectionFactory()
    return PostgresAccountRepository(db)


@pytest.fixture
def test_email() -> Email:
    """Provide a unique test email address for each test."""
    # Using timestamp-based email to avoid conflicts between test runs
    import time

    return Email(f"test-{int(time.time() * 1000)}@example.com")


@pytest.fixture
def test_password() -> Password:
    """Provide a test password (hashed)."""
    return Password.from_plain_text("SecurePass123!")


def test_create_account_persists_to_database(
    repository: PostgresAccountRepository,
    test_email: Email,
    test_password: Password,
) -> None:
    """
    PostgresAccountRepository.create() should persist account to database.

    Validates:
        - Account created successfully
        - Account is retrievable by email
        - Transaction committed automatically by repository
    """
    # Arrange
    account = Account.create(test_email, test_password)

    # Act
    repository.create(account)  # Commits automatically

    # Assert
    found_account = repository.find_by_email(test_email)
    assert found_account is not None
    assert found_account.email == test_email
    assert found_account.id == account.id


def test_create_account_with_duplicate_email_raises_integrity_error(
    repository: PostgresAccountRepository,
    test_email: Email,
    test_password: Password,
) -> None:
    """
    PostgresAccountRepository.create() should raise IntegrityError for duplicate email.

    Validates:
        - UNIQUE constraint on email is enforced
        - Database prevents duplicate emails
        - Error propagates to application layer
    """
    # Arrange
    account1 = Account.create(test_email, test_password)
    account2 = Account.create(test_email, test_password)  # Same email, different ID

    # Act & Assert
    repository.create(account1)  # Commits automatically

    # Attempt to create second account with same email
    with pytest.raises(IntegrityError):
        repository.create(account2)


def test_find_by_email_returns_account_when_found(
    repository: PostgresAccountRepository,
    test_email: Email,
    test_password: Password,
) -> None:
    """
    PostgresAccountRepository.find_by_email() should return account when found.

    Validates:
        - Account is retrievable after creation
        - Email search works correctly
        - Complete Account entity is returned
    """
    # Arrange
    account = Account.create(test_email, test_password)
    repository.create(account)  # Commits automatically

    # Act
    found_account = repository.find_by_email(test_email)

    # Assert
    assert found_account is not None
    assert found_account.id == account.id
    assert found_account.email == test_email
    assert found_account.is_activated is False


def test_find_by_email_returns_none_when_not_found(
    repository: PostgresAccountRepository,
) -> None:
    """
    PostgresAccountRepository.find_by_email() should return None when not found.

    Validates:
        - Returns None (not exception) for non-existent email
        - Handles "not found" gracefully
    """
    # Arrange
    non_existent_email = Email("nonexistent@example.com")

    # Act
    found_account = repository.find_by_email(non_existent_email)

    # Assert
    assert found_account is None


def test_round_trip_preserves_account_data(
    repository: PostgresAccountRepository,
    test_email: Email,
    test_password: Password,
) -> None:
    """
    Round-trip (entity → DB → entity) should preserve all account data.

    Validates:
        - Mapper correctly converts entity to row and back
        - Value objects are preserved (Email, Password, AccountId)
        - All account properties maintained
    """
    # Arrange
    original_account = Account.create(test_email, test_password)
    original_id = original_account.id
    original_email = original_account.email
    original_password_hash = original_account.password.hashed_value
    original_is_activated = original_account.is_activated

    # Act: Save to database (commits automatically)
    repository.create(original_account)

    # Act: Load from database
    retrieved_account = repository.find_by_email(test_email)

    # Assert: All properties preserved
    assert retrieved_account is not None
    assert retrieved_account.id == original_id
    assert retrieved_account.email == original_email
    assert retrieved_account.password.hashed_value == original_password_hash
    assert retrieved_account.is_activated == original_is_activated

    # Assert: Value objects preserved (type safety)
    assert isinstance(retrieved_account.email, Email)
    assert isinstance(retrieved_account.password, Password)


def test_find_by_email_is_case_insensitive(
    repository: PostgresAccountRepository,
    test_password: Password,
) -> None:
    """
    PostgresAccountRepository.find_by_email() should be case-insensitive.

    Validates:
        - Email VO normalizes to lowercase
        - Search works regardless of case
        - Database email stored as lowercase
    """
    # Arrange
    # Email VO normalizes to lowercase automatically
    import time

    unique_email_upper = f"TEST-{int(time.time() * 1000)}@EXAMPLE.COM"
    email_uppercase = Email(unique_email_upper)
    account = Account.create(email_uppercase, test_password)
    repository.create(account)  # Commits automatically

    # Act: Search with different case (Email VO normalizes both to lowercase)
    found_account = repository.find_by_email(Email(unique_email_upper.lower()))

    # Assert
    assert found_account is not None
    assert found_account.email.value == unique_email_upper.lower()  # Stored as lowercase
