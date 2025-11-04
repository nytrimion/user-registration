"""
Unit tests for account_activation_mapper.

Tests the bidirectional mapping between AccountActivation entities (domain) and
database rows (infrastructure). Validates type conversions, value object
preservation, timestamp handling, and round-trip consistency.

Test Strategy:
    - Unit tests (no database required)
    - Test to_persistence() conversion (entity → dict)
    - Test to_domain() conversion (dict → entity)
    - Test round-trip preservation (entity → dict → entity)
    - Test edge cases (UUID string/object handling, timestamp preservation)
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid7

from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.activation_code import ActivationCode
from src.account.infrastructure.persistence.account_activation_mapper import (
    to_domain,
    to_persistence,
)


def test_to_persistence_converts_activation_to_dict() -> None:
    """
    to_persistence() should convert AccountActivation entity to database-compatible dictionary.

    Validates:
        - account_id UUID converted to string
        - code extracted from value object
        - created_at timestamp preserved
        - expires_at timestamp preserved
    """
    # Arrange
    account_id = AccountId.generate()
    activation = AccountActivation.create_for_account(account_id)

    # Act
    row = to_persistence(activation)

    # Assert
    assert isinstance(row, dict)
    assert isinstance(row["account_id"], str)  # UUID converted to string
    assert isinstance(row["code"], str)
    assert len(row["code"]) == 4  # 4-digit code
    assert isinstance(row["created_at"], datetime)
    assert isinstance(row["expires_at"], datetime)


def test_to_persistence_preserves_uuid_value() -> None:
    """
    to_persistence() should preserve the UUID value when converting to string.

    Validates:
        - String UUID can be converted back to UUID object
        - No data loss during string conversion
    """
    # Arrange
    account_id = AccountId.generate()
    activation = AccountActivation.create_for_account(account_id)
    original_uuid = activation.account_id.value

    # Act
    row = to_persistence(activation)
    converted_uuid = UUID(row["account_id"])  # type: ignore[arg-type]

    # Assert
    assert converted_uuid == original_uuid


def test_to_persistence_preserves_timestamps() -> None:
    """
    to_persistence() should preserve created_at and expires_at timestamps.

    Validates:
        - Timestamps are datetime objects
        - expires_at is 60 seconds after created_at
    """
    # Arrange
    account_id = AccountId.generate()
    activation = AccountActivation.create_for_account(account_id)

    # Act
    row = to_persistence(activation)

    # Assert
    created_at = row["created_at"]
    expires_at = row["expires_at"]

    assert isinstance(created_at, datetime)
    assert isinstance(expires_at, datetime)

    # Validate 60-second expiration (with small tolerance for test execution time)
    time_diff = expires_at - created_at
    assert 59 <= time_diff.total_seconds() <= 61


def test_to_domain_converts_dict_to_activation() -> None:
    """
    to_domain() should convert database row dictionary to AccountActivation entity.

    Validates:
        - String UUID converted to AccountId value object
        - Code string converted to ActivationCode value object
        - Timestamps preserved as datetime objects
    """
    # Arrange
    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(seconds=60)
    row = {
        "account_id": "019a4ba0-9bf9-71c9-91b2-b51c4e875388",
        "code": "1234",
        "created_at": created_at,
        "expires_at": expires_at,
    }

    # Act
    activation = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert isinstance(activation, AccountActivation)
    assert isinstance(activation.account_id, AccountId)
    assert isinstance(activation.code, ActivationCode)
    assert activation.code.code == "1234"
    assert activation.created_at == created_at
    assert activation.expires_at == expires_at


def test_to_domain_handles_uuid_object() -> None:
    """
    to_domain() should handle UUID objects (not just strings).

    Validates:
        - Accepts both UUID and string for account_id field
        - Handles UUID objects gracefully
    """
    # Arrange
    uuid_obj = uuid7()
    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(seconds=60)
    row = {
        "account_id": uuid_obj,  # UUID object instead of string
        "code": "5678",
        "created_at": created_at,
        "expires_at": expires_at,
    }

    # Act
    activation = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert activation.account_id.value == uuid_obj


def test_to_domain_handles_uuid_string() -> None:
    """
    to_domain() should convert string UUID to UUID object.

    Validates:
        - String UUID converted to proper UUID object
        - UUID validation occurs
    """
    # Arrange
    uuid_str = "019a4ba0-9bf9-71c9-91b2-b51c4e875388"
    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(seconds=60)
    row = {
        "account_id": uuid_str,
        "code": "9999",
        "created_at": created_at,
        "expires_at": expires_at,
    }

    # Act
    activation = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert isinstance(activation.account_id.value, UUID)
    assert str(activation.account_id.value) == uuid_str


def test_round_trip_preserves_activation_data() -> None:
    """
    Round-trip (entity → dict → entity) should preserve all activation data.

    Validates:
        - to_persistence() followed by to_domain() preserves data
        - No data loss during conversions
        - Value objects correctly reconstructed
        - Timestamps preserved with microsecond precision
    """
    # Arrange
    original_account_id = AccountId.generate()
    original_activation = AccountActivation.create_for_account(original_account_id)

    # Act: Convert to persistence
    row = to_persistence(original_activation)

    # Act: Convert back to domain
    reconstructed_activation = to_domain(row)  # type: ignore[arg-type]

    # Assert: All data preserved
    assert reconstructed_activation.account_id == original_account_id
    assert reconstructed_activation.code == original_activation.code
    assert reconstructed_activation.created_at == original_activation.created_at
    assert reconstructed_activation.expires_at == original_activation.expires_at


def test_to_persistence_extracts_code_value() -> None:
    """
    to_persistence() should extract the string value from ActivationCode VO.

    Validates:
        - Code is stored as plain string (not value object)
        - Code is 4-digit numeric string
    """
    # Arrange
    account_id = AccountId.generate()
    activation = AccountActivation.create_for_account(account_id)

    # Act
    row = to_persistence(activation)

    # Assert
    code = row["code"]
    assert isinstance(code, str)
    assert len(code) == 4
    assert code.isdigit()


def test_to_domain_validates_code_via_value_object() -> None:
    """
    to_domain() should reconstruct ActivationCode value object (with validation).

    Validates:
        - Code string converted to ActivationCode VO
        - Value object validation occurs during reconstruction
    """
    # Arrange
    created_at = datetime.now(UTC)
    expires_at = created_at + timedelta(seconds=60)
    row = {
        "account_id": str(uuid7()),
        "code": "4321",  # Valid 4-digit code
        "created_at": created_at,
        "expires_at": expires_at,
    }

    # Act
    activation = to_domain(row)  # type: ignore[arg-type]

    # Assert
    assert isinstance(activation.code, ActivationCode)
    assert activation.code.code == "4321"


def test_to_domain_preserves_expiration_logic() -> None:
    """
    to_domain() should preserve expiration timestamps for business logic.

    Validates:
        - expires_at correctly mapped
        - Expiration logic can be evaluated after reconstruction
    """
    # Arrange: Create expired activation (created 70 seconds ago)
    created_at = datetime.now(UTC) - timedelta(seconds=70)
    expires_at = created_at + timedelta(seconds=60)
    row = {
        "account_id": str(uuid7()),
        "code": "0000",
        "created_at": created_at,
        "expires_at": expires_at,
    }

    # Act
    activation = to_domain(row)  # type: ignore[arg-type]

    # Assert: Activation is expired (business logic works)
    assert activation.is_expired() is True


def test_to_domain_with_non_expired_activation() -> None:
    """
    to_domain() should correctly reconstruct non-expired activations.

    Validates:
        - Recent activation is not expired
        - Expiration logic works for valid codes
    """
    # Arrange: Create recent activation (created 10 seconds ago)
    created_at = datetime.now(UTC) - timedelta(seconds=10)
    expires_at = created_at + timedelta(seconds=60)
    row = {
        "account_id": str(uuid7()),
        "code": "7777",
        "created_at": created_at,
        "expires_at": expires_at,
    }

    # Act
    activation = to_domain(row)  # type: ignore[arg-type]

    # Assert: Activation is NOT expired
    assert activation.is_expired() is False
