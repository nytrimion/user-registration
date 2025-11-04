"""
Integration tests for PostgresAccountActivationRepository.

These tests validate the repository behavior with a real PostgreSQL database.
They ensure proper UPSERT operations, FK constraints, and entity round-trip.

Test Strategy:
    - Real PostgreSQL database (Docker service)
    - Test CRUD operations (save, find_by_account_id)
    - Test UPSERT behavior (one code per account)
    - Test round-trip (entity → DB → entity preserves data)
    - Test FK constraint (activation requires existing account)
    - Repository commits automatically (no manual commit needed)

Database:
    - Uses DATABASE_* environment variables (same as application)
    - Tests run against real PostgreSQL instance
    - Repository commits transactions automatically
    - Tests are independent (no shared state)

Fixtures:
    - account_repository: PostgresAccountRepository for creating test accounts
    - activation_repository: PostgresAccountActivationRepository to test
    - test_account: Sample Account entity for testing
"""

import pytest

from src.account.domain.entities.account import Account
from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.infrastructure.persistence.postgres_account_activation_repository import (
    PostgresAccountActivationRepository,
)
from src.account.infrastructure.persistence.postgres_account_repository import (
    PostgresAccountRepository,
)
from src.shared.infrastructure.database.connection import PostgresConnectionFactory


@pytest.fixture
def account_repository() -> PostgresAccountRepository:
    """
    Provide PostgresAccountRepository for creating test accounts.

    AccountActivation has FK to account.id, so we need to create
    accounts before creating activations.

    Returns:
        PostgresAccountRepository: Repository for account creation
    """
    db = PostgresConnectionFactory()
    return PostgresAccountRepository(db)


@pytest.fixture
def activation_repository() -> PostgresAccountActivationRepository:
    """
    Provide PostgresAccountActivationRepository with real connection pool.

    Creates a repository instance connected to the test database.
    Each test gets a fresh repository instance.

    Returns:
        PostgresAccountActivationRepository: Repository with real PostgreSQL connection
    """
    db = PostgresConnectionFactory()
    return PostgresAccountActivationRepository(db)


@pytest.fixture
def test_account(account_repository: PostgresAccountRepository) -> Account:
    """
    Provide a persisted test account for activation tests.

    Creates and persists an account in the database. This account
    is used as the FK target for account_activation records.

    Args:
        account_repository: Repository for persisting the account

    Returns:
        Account: Persisted account entity
    """
    import time

    email = Email(f"test-{int(time.time() * 1000)}@example.com")
    password = Password.from_plain_text("SecurePass123!")
    account = Account.create(email, password)

    # Persist account (required for FK constraint)
    account_repository.save(account)

    return account


def test_save_creates_activation_in_database(
    activation_repository: PostgresAccountActivationRepository,
    test_account: Account,
) -> None:
    """
    PostgresAccountActivationRepository.save() should persist activation to database.

    Validates:
        - Activation created successfully
        - Activation is retrievable by account_id
        - Transaction committed automatically by repository
    """
    # Arrange
    activation = AccountActivation.create_for_account(test_account.id)

    # Act
    activation_repository.save(activation)  # Commits automatically

    # Assert
    found_activation = activation_repository.find_by_account_id(test_account.id)
    assert found_activation is not None
    assert found_activation.account_id == test_account.id
    assert found_activation.code == activation.code


def test_save_replaces_existing_activation_for_same_account(
    activation_repository: PostgresAccountActivationRepository,
    test_account: Account,
) -> None:
    """
    PostgresAccountActivationRepository.save() should replace existing activation (UPSERT).

    Validates:
        - UPSERT pattern works correctly (ON CONFLICT account_id)
        - Second save() replaces first activation
        - Business rule enforced: one code per account
    """
    # Arrange
    first_activation = AccountActivation.create_for_account(test_account.id)
    second_activation = AccountActivation.create_for_account(test_account.id)

    # Act: Save first activation
    activation_repository.save(first_activation)  # Commits automatically

    # Act: Save second activation (should replace first)
    activation_repository.save(second_activation)  # Commits automatically

    # Assert: Only second activation exists
    found_activation = activation_repository.find_by_account_id(test_account.id)
    assert found_activation is not None
    assert found_activation.code == second_activation.code
    assert found_activation.code != first_activation.code  # First code replaced


def test_find_by_account_id_returns_activation_when_found(
    activation_repository: PostgresAccountActivationRepository,
    test_account: Account,
) -> None:
    """
    PostgresAccountActivationRepository.find_by_account_id() should return activation when found.

    Validates:
        - Activation is retrievable after creation
        - account_id search works correctly
        - Complete AccountActivation entity is returned
    """
    # Arrange
    activation = AccountActivation.create_for_account(test_account.id)
    activation_repository.save(activation)  # Commits automatically

    # Act
    found_activation = activation_repository.find_by_account_id(test_account.id)

    # Assert
    assert found_activation is not None
    assert found_activation.account_id == test_account.id
    assert found_activation.code == activation.code


def test_find_by_account_id_returns_none_when_not_found(
    activation_repository: PostgresAccountActivationRepository,
    test_account: Account,
) -> None:
    """
    PostgresAccountActivationRepository.find_by_account_id() should return None when not found.

    Validates:
        - Returns None (not exception) for non-existent account_id
        - Handles "not found" gracefully
    """
    # Act: Search for activation that doesn't exist
    found_activation = activation_repository.find_by_account_id(test_account.id)

    # Assert
    assert found_activation is None


def test_round_trip_preserves_activation_data(
    activation_repository: PostgresAccountActivationRepository,
    test_account: Account,
) -> None:
    """
    Round-trip (entity → DB → entity) should preserve all activation data.

    Validates:
        - Mapper correctly converts entity to row and back
        - Value objects are preserved (AccountId, ActivationCode)
        - Timestamps are preserved (created_at, expires_at)
    """
    # Arrange
    original_activation = AccountActivation.create_for_account(test_account.id)
    original_account_id = original_activation.account_id
    original_code = original_activation.code
    original_created_at = original_activation.created_at
    original_expires_at = original_activation.expires_at

    # Act: Save to database (commits automatically)
    activation_repository.save(original_activation)

    # Act: Load from database
    retrieved_activation = activation_repository.find_by_account_id(test_account.id)

    # Assert: All properties preserved
    assert retrieved_activation is not None
    assert retrieved_activation.account_id == original_account_id
    assert retrieved_activation.code == original_code

    # Assert: Timestamps preserved (with microsecond precision tolerance)
    # PostgreSQL TIMESTAMPTZ has microsecond precision, Python datetime also
    assert retrieved_activation.created_at == original_created_at
    assert retrieved_activation.expires_at == original_expires_at

    # Assert: Value objects preserved (type safety)
    from src.account.domain.value_objects.account_id import AccountId
    from src.account.domain.value_objects.activation_code import ActivationCode

    assert isinstance(retrieved_activation.account_id, AccountId)
    assert isinstance(retrieved_activation.code, ActivationCode)


def test_save_raises_foreign_key_error_for_nonexistent_account(
    activation_repository: PostgresAccountActivationRepository,
) -> None:
    """
    PostgresAccountActivationRepository.save() should raise error for non-existent account_id.

    Validates:
        - Foreign key constraint enforced (account_id must exist in account table)
        - Database prevents orphaned activations
    """
    from psycopg2 import IntegrityError

    from src.account.domain.value_objects.account_id import AccountId

    # Arrange: Create activation for non-existent account
    non_existent_account_id = AccountId.generate()
    activation = AccountActivation.create_for_account(non_existent_account_id)

    # Act & Assert: Save should raise IntegrityError (FK violation)
    with pytest.raises(IntegrityError):
        activation_repository.save(activation)
