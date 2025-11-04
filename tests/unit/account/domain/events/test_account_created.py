"""
Unit tests for AccountCreated domain event.

Tests verify:
    - Immutability (frozen dataclass)
    - Attribute accessibility
    - Correct value object types
"""

from datetime import UTC, datetime

import pytest

from src.account.domain.events.account_created import AccountCreated
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email


class TestAccountCreated:
    """Test suite for AccountCreated domain event."""

    def test_account_created_has_correct_attributes(self) -> None:
        """Verify AccountCreated event has all required attributes."""
        # Arrange
        account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
        email = Email("user@example.com")
        occurred_at = datetime.now(UTC)

        # Act
        event = AccountCreated(account_id=account_id, email=email, occurred_at=occurred_at)

        # Assert
        assert event.account_id == account_id
        assert event.email == email
        assert event.occurred_at == occurred_at

    def test_account_created_is_immutable(self) -> None:
        """Verify AccountCreated event cannot be modified after creation."""
        # Arrange
        event = AccountCreated(
            account_id=AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc"),
            email=Email("user@example.com"),
            occurred_at=datetime.now(UTC),
        )

        # Act & Assert
        with pytest.raises(AttributeError):
            event.account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-000000000000")  # type: ignore[misc]

        with pytest.raises(AttributeError):
            event.email = Email("other@example.com")  # type: ignore[misc]

        with pytest.raises(AttributeError):
            event.occurred_at = datetime.now(UTC)  # type: ignore[misc]

    def test_account_created_uses_value_objects(self) -> None:
        """Verify AccountCreated uses value objects instead of primitives."""
        # Arrange & Act
        event = AccountCreated(
            account_id=AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc"),
            email=Email("user@example.com"),
            occurred_at=datetime.now(UTC),
        )

        # Assert
        assert isinstance(event.account_id, AccountId)
        assert isinstance(event.email, Email)
        assert isinstance(event.occurred_at, datetime)
