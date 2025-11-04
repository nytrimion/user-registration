"""
Unit tests for ActivateAccountHandler.

Tests the use case handler's orchestration of account activation workflow.
Uses mocks for repositories to isolate business logic.

Test Strategy:
    - Unit tests (no database)
    - Mock AccountRepository and AccountActivationRepository
    - Verify workflow orchestration (load → validate → activate → save)
    - Validate error handling (not found, expired, invalid code)
    - Test idempotence (already active accounts)
    - Test validation order (fail fast)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import Mock

import pytest

from src.account.application.commands.activate_account import (
    ActivateAccountCommand,
    ActivateAccountHandler,
)
from src.account.domain.entities.account import Account
from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.exceptions import (
    AccountNotFoundError,
    ActivationCodeExpiredError,
    ActivationCodeNotFoundError,
    InvalidActivationCodeError,
)
from src.account.domain.repositories.account_activation_repository import (
    AccountActivationRepository,
)
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.value_objects.activation_code import ActivationCode
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password


@pytest.fixture
def mock_account_repository() -> Mock:
    """Provide mock AccountRepository."""
    return Mock(spec=AccountRepository)


@pytest.fixture
def mock_activation_repository() -> Mock:
    """Provide mock AccountActivationRepository."""
    return Mock(spec=AccountActivationRepository)


@pytest.fixture
def handler(
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
) -> ActivateAccountHandler:
    """Provide ActivateAccountHandler with mocked dependencies."""
    return ActivateAccountHandler(
        mock_account_repository,
        mock_activation_repository,
    )


@pytest.fixture
def sample_account() -> Account:
    """Provide inactive account for tests."""
    return Account.create(
        Email("user@example.com"),
        Password.from_plain_text("SecurePass123"),
    )


@pytest.fixture
def sample_activation(sample_account: Account) -> AccountActivation:
    """Provide non-expired activation code."""
    return AccountActivation.create_for_account(sample_account.id)


@pytest.fixture
def activate_command(
    sample_account: Account, sample_activation: AccountActivation
) -> ActivateAccountCommand:
    """Provide valid ActivateAccountCommand."""
    return ActivateAccountCommand(
        account_id=sample_account.id,
        code=sample_activation.code,
    )


def test_handle_activates_account_when_valid(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
    sample_activation: AccountActivation,
    activate_command: ActivateAccountCommand,
) -> None:
    """
    handle() should activate account when code valid.

    Validates:
        - Account loaded from repository
        - Activation code loaded
        - account.activate() called
        - Account saved to repository
    """
    # Arrange
    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = sample_activation

    # Act
    handler.handle(activate_command)

    # Assert: Account loaded
    mock_account_repository.find_by_id.assert_called_once_with(sample_account.id)

    # Assert: Activation loaded
    mock_activation_repository.find_by_account_id.assert_called_once_with(sample_account.id)

    # Assert: Account activated (is_activated = True)
    assert sample_account.is_activated is True

    # Assert: Account saved
    mock_account_repository.save.assert_called_once_with(sample_account)


def test_handle_raises_when_account_not_found(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    activate_command: ActivateAccountCommand,
) -> None:
    """handle() should raise AccountNotFoundError when account does not exist."""
    # Arrange
    mock_account_repository.find_by_id.return_value = None

    # Act & Assert
    with pytest.raises(AccountNotFoundError, match="not found"):
        handler.handle(activate_command)


def test_handle_raises_when_activation_code_not_found(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
    activate_command: ActivateAccountCommand,
) -> None:
    """handle() should raise ActivationCodeNotFoundError when no code exists."""
    # Arrange
    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = None

    # Act & Assert
    with pytest.raises(ActivationCodeNotFoundError, match="No activation code"):
        handler.handle(activate_command)


def test_handle_raises_when_code_expired(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
    activate_command: ActivateAccountCommand,
) -> None:
    """handle() should raise ActivationCodeExpiredError when code expired."""
    # Arrange: Create expired activation (61 seconds ago)
    created_at = datetime.now(UTC) - timedelta(seconds=61)
    expired_activation = AccountActivation(
        _account_id=sample_account.id,
        _code=ActivationCode.generate(),
        _created_at=created_at,
        _expires_at=created_at + timedelta(seconds=60),
    )

    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = expired_activation

    # Act & Assert
    with pytest.raises(ActivationCodeExpiredError, match="expired"):
        handler.handle(activate_command)


def test_handle_raises_when_code_value_mismatch(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
    sample_activation: AccountActivation,
) -> None:
    """handle() should raise InvalidActivationCodeError when code mismatch."""
    # Arrange: Command with wrong code
    wrong_command = ActivateAccountCommand(
        account_id=sample_account.id,
        code=ActivationCode("9999"),  # Wrong code
    )

    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = sample_activation

    # Act & Assert
    with pytest.raises(InvalidActivationCodeError, match="Invalid"):
        handler.handle(wrong_command)


def test_handle_is_idempotent_when_already_active(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
    sample_activation: AccountActivation,
    activate_command: ActivateAccountCommand,
) -> None:
    """handle() should succeed without error when account already active."""
    # Arrange: Already active account
    sample_account.activate()  # Manually activate
    assert sample_account.is_activated is True

    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = sample_activation

    # Act: Should not raise
    handler.handle(activate_command)

    # Assert: Still active, saved again (idempotent)
    assert sample_account.is_activated is True
    mock_account_repository.save.assert_called_once()


def test_handle_validates_account_before_code(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    activate_command: ActivateAccountCommand,
) -> None:
    """handle() should validate account exists before loading activation code."""
    # Arrange: Account not found
    mock_account_repository.find_by_id.return_value = None

    # Act & Assert: Should raise before checking activation code
    with pytest.raises(AccountNotFoundError):
        handler.handle(activate_command)

    # Assert: Activation repository never called
    mock_activation_repository.find_by_account_id.assert_not_called()


def test_handle_validates_expiration_before_value(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
) -> None:
    """handle() should check expiration before code value."""
    # Arrange: Expired code with wrong value
    created_at = datetime.now(UTC) - timedelta(seconds=61)
    expired_activation = AccountActivation(
        _account_id=sample_account.id,
        _code=ActivationCode.generate(),
        _created_at=created_at,
        _expires_at=created_at + timedelta(seconds=60),
    )

    wrong_command = ActivateAccountCommand(
        account_id=sample_account.id,
        code=ActivationCode("9999"),  # Wrong code (but expired takes precedence)
    )

    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = expired_activation

    # Act & Assert: Should raise ActivationCodeExpiredError (not Invalid)
    with pytest.raises(ActivationCodeExpiredError):
        handler.handle(wrong_command)


def test_handle_does_not_save_when_validation_fails(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
) -> None:
    """handle() should not save account when validation fails."""
    # Arrange: No activation code
    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = None

    command = ActivateAccountCommand(
        account_id=sample_account.id,
        code=ActivationCode("1234"),
    )

    # Act & Assert
    with pytest.raises(ActivationCodeNotFoundError):
        handler.handle(command)

    # Assert: Save never called
    mock_account_repository.save.assert_not_called()


def test_handle_compares_activation_code_value_objects(
    handler: ActivateAccountHandler,
    mock_account_repository: Mock,
    mock_activation_repository: Mock,
    sample_account: Account,
) -> None:
    """handle() should compare ActivationCode VOs using __eq__."""
    # Arrange: Matching codes (both are ActivationCode VOs)
    code_value = "1234"
    created_at = datetime.now(UTC)
    activation = AccountActivation(
        _account_id=sample_account.id,
        _code=ActivationCode(code_value),
        _created_at=created_at,
        _expires_at=created_at + timedelta(seconds=60),
    )
    command = ActivateAccountCommand(
        account_id=sample_account.id,
        code=ActivationCode(code_value),  # Same value, different object
    )

    mock_account_repository.find_by_id.return_value = sample_account
    mock_activation_repository.find_by_account_id.return_value = activation

    # Act: Should succeed (ActivationCode.__eq__ compares .code values)
    handler.handle(command)

    # Assert: Account activated and saved
    assert sample_account.is_activated is True
    mock_account_repository.save.assert_called_once()
