"""
Unit tests for AccountActivation entity.

Tests verify:
    - Factory method creates activation with correct expiration
    - Expiration logic (60 seconds)
    - Validation logic (code match + not expired)
    - Encapsulation (property access, no direct modification)
    - Entity identity (__eq__, __hash__ by account_id)
"""

from datetime import UTC, datetime, timedelta

import pytest

from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.activation_code import ActivationCode


class TestAccountActivation:
    """Test suite for AccountActivation entity."""

    def test_create_for_account_generates_activation_with_code(self) -> None:
        """Verify factory creates activation with generated code."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")

        # Act
        activation = AccountActivation.create_for_account(account_id)

        # Assert
        assert activation.account_id == account_id
        assert isinstance(activation.code, ActivationCode)

    def test_create_for_account_sets_expiration_to_60_seconds(self) -> None:
        """Verify factory sets expiration to 60 seconds from creation."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        before_creation = datetime.now(UTC)

        # Act
        activation = AccountActivation.create_for_account(account_id)

        # Assert
        after_creation = datetime.now(UTC)
        expected_expiration = activation.created_at + timedelta(seconds=60)

        assert activation.expires_at == expected_expiration
        assert before_creation <= activation.created_at <= after_creation
        assert activation.expires_at > activation.created_at

    def test_is_expired_returns_false_before_expiration(self) -> None:
        """Verify is_expired() returns False before 60 seconds."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        activation = AccountActivation.create_for_account(account_id)

        # Act & Assert
        assert activation.is_expired() is False

    def test_is_expired_returns_true_after_expiration(self) -> None:
        """Verify is_expired() returns True after 60 seconds."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")

        # Create activation with past expiration (simulate expired)
        code = ActivationCode("1234")
        created_at = datetime.now(UTC) - timedelta(seconds=61)
        expires_at = created_at + timedelta(seconds=60)

        activation = AccountActivation(
            _account_id=account_id,
            _code=code,
            _created_at=created_at,
            _expires_at=expires_at,
        )

        # Act & Assert
        assert activation.is_expired() is True

    def test_is_valid_returns_true_for_matching_code_and_not_expired(self) -> None:
        """Verify is_valid() returns True when code matches and not expired."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        code = ActivationCode("1234")
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(seconds=60)

        activation = AccountActivation(
            _account_id=account_id,
            _code=code,
            _created_at=created_at,
            _expires_at=expires_at,
        )

        # Act & Assert
        assert activation.is_valid("1234") is True

    def test_is_valid_returns_false_for_incorrect_code(self) -> None:
        """Verify is_valid() returns False when code does not match."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        code = ActivationCode("1234")
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(seconds=60)

        activation = AccountActivation(
            _account_id=account_id,
            _code=code,
            _created_at=created_at,
            _expires_at=expires_at,
        )

        # Act & Assert
        assert activation.is_valid("5678") is False

    def test_is_valid_returns_false_for_expired_activation(self) -> None:
        """Verify is_valid() returns False when activation has expired."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        code = ActivationCode("1234")
        created_at = datetime.now(UTC) - timedelta(seconds=61)
        expires_at = created_at + timedelta(seconds=60)

        activation = AccountActivation(
            _account_id=account_id,
            _code=code,
            _created_at=created_at,
            _expires_at=expires_at,
        )

        # Act & Assert
        assert activation.is_valid("1234") is False  # Correct code but expired

    def test_properties_are_accessible(self) -> None:
        """Verify all properties are accessible via getters."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        activation = AccountActivation.create_for_account(account_id)

        # Act & Assert
        assert activation.account_id == account_id
        assert isinstance(activation.code, ActivationCode)
        assert isinstance(activation.created_at, datetime)
        assert isinstance(activation.expires_at, datetime)

    def test_account_activation_properties_are_read_only(self) -> None:
        """Verify properties cannot be modified (encapsulation)."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        activation = AccountActivation.create_for_account(account_id)

        # Act & Assert - Properties are read-only
        with pytest.raises(AttributeError):
            activation.account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-000000000000")  # type: ignore[misc]

        with pytest.raises(AttributeError):
            activation.code = ActivationCode("5678")  # type: ignore[misc]

        with pytest.raises(AttributeError):
            activation.created_at = datetime.now(UTC)  # type: ignore[misc]

        with pytest.raises(AttributeError):
            activation.expires_at = datetime.now(UTC)  # type: ignore[misc]

    def test_entity_equality_based_on_account_id(self) -> None:
        """Verify entity equality is based on account_id (identity)."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        activation1 = AccountActivation.create_for_account(account_id)
        activation2 = AccountActivation.create_for_account(account_id)

        # Act & Assert - Same account_id = equal entities
        assert activation1 == activation2

    def test_entity_inequality_for_different_account_ids(self) -> None:
        """Verify entities with different account_ids are not equal."""
        # Arrange
        account_id1 = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        account_id2 = AccountId.from_string("0192a4e3-7890-7bcd-8000-000000000001")

        activation1 = AccountActivation.create_for_account(account_id1)
        activation2 = AccountActivation.create_for_account(account_id2)

        # Act & Assert
        assert activation1 != activation2

    def test_entity_hash_based_on_account_id(self) -> None:
        """Verify entity hash is based on account_id (allows use in sets/dicts)."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        activation1 = AccountActivation.create_for_account(account_id)
        activation2 = AccountActivation.create_for_account(account_id)

        # Act & Assert - Same account_id = same hash
        assert hash(activation1) == hash(activation2)

        # Can be used in set
        activation_set = {activation1, activation2}
        assert len(activation_set) == 1  # Only one unique entity
