"""
Unit tests for account_mapper.

Tests the bidirectional mapping between Account entities (domain) and
database rows (infrastructure). Validates type conversions, value object
preservation, and round-trip consistency.

Test Strategy:
    - Unit tests (no database required)
    - Test to_persistence() conversion (entity → dict)
    - Test to_domain() conversion (dict → entity)
    - Test round-trip preservation (entity → dict → entity)
    - Test edge cases (UUID string/object handling)
"""

from datetime import UTC, datetime
from uuid import UUID, uuid7

from src.account.domain.entities.account import Account
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.infrastructure.persistence.account_mapper import (
    to_domain,
    to_persistence,
)


def test_to_persistence_converts_account_to_dict() -> None:
    """
    to_persistence() should convert Account entity to database-compatible dictionary.

    Validates:
        - UUID converted to string
        - Email extracted from value object
        - Password hash extracted
        - is_activated boolean preserved
    """
    # Arrange
    email = Email("test@example.com")
    password = Password.from_plain_text("SecurePass123!")
    account = Account.create(email, password)

    # Act
    row = to_persistence(account)

    # Assert
    assert isinstance(row, dict)
    assert isinstance(row["id"], str)  # UUID converted to string
    assert row["email"] == "test@example.com"
    assert isinstance(row["password_hash"], str)
    assert row["password_hash"].startswith("$2b$")  # bcrypt hash
    assert row["is_activated"] is False


def test_to_persistence_preserves_uuid_value() -> None:
    """
    to_persistence() should preserve the UUID value when converting to string.

    Validates:
        - String UUID can be converted back to UUID object
        - No data loss during string conversion
    """
    # Arrange
    email = Email("test@example.com")
    password = Password.from_plain_text("Password123!")
    account = Account.create(email, password)
    original_uuid = account.id.value

    # Act
    row = to_persistence(account)
    converted_uuid = UUID(row["id"])  # type: ignore[arg-type]

    # Assert
    assert converted_uuid == original_uuid


def test_to_domain_converts_dict_to_account() -> None:
    """
    to_domain() should convert database row dictionary to Account entity.

    Validates:
        - String UUID converted to AccountId value object
        - Email string converted to Email value object
        - Password hash converted to Password value object
        - Boolean preserved
    """
    # Arrange
    row = {
        "id": "019a4ba0-9bf9-71c9-91b2-b51c4e875388",
        "email": "test@example.com",
        "password_hash": "$2b$12$abcdefghijklmnopqrstuv",
        "is_activated": False,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Act
    account = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert isinstance(account, Account)
    assert isinstance(account.id, AccountId)
    assert isinstance(account.email, Email)
    assert isinstance(account.password, Password)
    assert account.email.value == "test@example.com"
    assert account.password.hashed_value == "$2b$12$abcdefghijklmnopqrstuv"
    assert account.is_activated is False


def test_to_domain_handles_uuid_object() -> None:
    """
    to_domain() should handle UUID objects (not just strings).

    Validates:
        - Accepts both UUID and string for id field
        - Handles UUID objects gracefully
    """
    # Arrange
    uuid_obj = uuid7()
    row = {
        "id": uuid_obj,  # UUID object instead of string
        "email": "test@example.com",
        "password_hash": "$2b$12$abcdefghijklmnopqrstuv",
        "is_activated": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Act
    account = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert account.id.value == uuid_obj


def test_to_domain_handles_uuid_string() -> None:
    """
    to_domain() should convert string UUID to UUID object.

    Validates:
        - String UUID converted to proper UUID object
        - UUID validation occurs
    """
    # Arrange
    uuid_str = "019a4ba0-9bf9-71c9-91b2-b51c4e875388"
    row = {
        "id": uuid_str,
        "email": "test@example.com",
        "password_hash": "$2b$12$hash",
        "is_activated": False,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Act
    account = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert isinstance(account.id.value, UUID)
    assert str(account.id.value) == uuid_str


def test_round_trip_preserves_account_data() -> None:
    """
    Round-trip (entity → dict → entity) should preserve all account data.

    Validates:
        - to_persistence() followed by to_domain() preserves data
        - No data loss during conversions
        - Value objects correctly reconstructed
    """
    # Arrange
    original_email = Email("roundtrip@example.com")
    original_password = Password.from_plain_text("MyPassword123!")
    original_account = Account.create(original_email, original_password)

    # Act: Convert to persistence
    row = to_persistence(original_account)

    # Simulate database storage (add timestamps like DB would)
    row_with_timestamps = {
        **row,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Act: Convert back to domain
    reconstructed_account = to_domain(row_with_timestamps)  # type: ignore[arg-type]

    # Assert: All data preserved
    assert reconstructed_account.id == original_account.id
    assert reconstructed_account.email == original_email
    assert reconstructed_account.password.hashed_value == original_password.hashed_value
    assert reconstructed_account.is_activated == original_account.is_activated


def test_to_persistence_handles_activated_account() -> None:
    """
    to_persistence() should handle activated accounts correctly.

    Validates:
        - is_activated=True preserved
    """
    # Arrange
    email = Email("activated@example.com")
    password = Password.from_plain_text("Password123!")
    account = Account.create(email, password)
    account.activate()  # Activate the account

    # Act
    row = to_persistence(account)

    # Assert
    assert row["is_activated"] is True


def test_to_domain_preserves_activated_status() -> None:
    """
    to_domain() should preserve activated account status.

    Validates:
        - is_activated=True correctly mapped
    """
    # Arrange
    row = {
        "id": str(uuid7()),
        "email": "active@example.com",
        "password_hash": "$2b$12$hash",
        "is_activated": True,  # Activated account
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }

    # Act
    account = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert account.is_activated is True
