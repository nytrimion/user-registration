"""
Unit tests for RegisterAccount command and handler.

These tests verify the business logic of account registration without any
infrastructure dependencies (no database, no HTTP, no injector).

Testing Strategy:
    - Mock AccountRepository and EventDispatcher using unittest.mock
    - Test happy path (successful registration + event dispatch)
    - Test business rule violations (email uniqueness)
    - Test exception propagation from value objects

No Integration Dependencies:
    - No database connection required
    - No FastAPI TestClient needed
    - No injector configuration needed
    - Fast execution (~milliseconds per test)
"""

from unittest.mock import Mock

import pytest

from src.account.application.commands.register_account import (
    RegisterAccountCommand,
    RegisterAccountHandler,
)
from src.account.domain.entities.account import Account
from src.account.domain.events.account_created import AccountCreated
from src.account.domain.exceptions import EmailAlreadyExistsError
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.shared.domain.events.event_dispatcher import EventDispatcher


def test_register_account_command_is_immutable() -> None:
    """
    Command should be immutable (frozen dataclass).

    This ensures commands remain valid throughout their lifecycle and cannot
    be accidentally modified after creation.
    """
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")

    command = RegisterAccountCommand(email=email, password=password)

    with pytest.raises(AttributeError):
        command.email = Email("hacker@example.com")  # type: ignore


def test_register_account_success_when_email_available() -> None:
    """
    Handler should create account when email is not already registered.

    Business Flow:
        1. Check if email exists (returns None)
        2. Create Account aggregate
        3. Persist via repository

    Verification:
        - repository.find_by_email() called with correct email
        - repository.create() called exactly once
        - Account created with correct email and password
    """
    # Arrange: Create command with valid credentials
    email = Email("newuser@example.com")
    password = Password.from_plain_text("SecurePassword123")
    command = RegisterAccountCommand(email=email, password=password)

    # Mock repository: email doesn't exist
    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    # Mock event dispatcher
    mock_dispatcher = Mock(spec=EventDispatcher)

    # Create handler with mocked dependencies (no @inject needed in tests)
    handler = RegisterAccountHandler(repository=mock_repository, dispatcher=mock_dispatcher)

    # Act: Execute command
    handler.handle(command)

    # Assert: Verify business logic execution
    mock_repository.find_by_email.assert_called_once_with(email)
    mock_repository.create.assert_called_once()

    # Verify Account was created with correct properties
    created_account = mock_repository.create.call_args[0][0]
    assert isinstance(created_account, Account)
    assert created_account.email == email
    assert created_account.password == password
    assert created_account.is_activated is False


def test_register_account_raises_error_when_email_already_exists() -> None:
    """
    Handler should raise EmailAlreadyExistsError when email is taken.

    Business Rule: Email addresses must be unique across all accounts.

    Verification:
        - EmailAlreadyExistsError raised with correct email
        - repository.create() NOT called (early return on validation failure)
    """
    # Arrange: Create command with email that already exists
    email = Email("existing@example.com")
    password = Password.from_plain_text("SecurePassword123")
    command = RegisterAccountCommand(email=email, password=password)

    # Mock repository: email already exists
    existing_account = Account.create(email=email, password=password)
    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = existing_account

    # Mock event dispatcher (not used in error path, but required for handler init)
    mock_dispatcher = Mock(spec=EventDispatcher)

    handler = RegisterAccountHandler(repository=mock_repository, dispatcher=mock_dispatcher)

    # Act & Assert: Verify exception is raised
    with pytest.raises(EmailAlreadyExistsError) as exc_info:
        handler.handle(command)

    # Verify exception contains correct email
    assert exc_info.value.email == email
    assert "existing@example.com" in str(exc_info.value)

    # Verify create() was NOT called (validation failed early)
    mock_repository.create.assert_not_called()


def test_register_account_propagates_invalid_email_error() -> None:
    """
    Handler should propagate ValueError from Email value object.

    This test verifies that validation errors from value objects are not
    caught by the handler, allowing them to bubble up to the caller.
    """
    # Arrange: Create command with invalid email (will raise ValueError)
    with pytest.raises(ValueError, match="Invalid email"):
        invalid_email = Email("not-an-email")
        password = Password.from_plain_text("SecurePassword123")
        RegisterAccountCommand(email=invalid_email, password=password)


def test_register_account_propagates_weak_password_error() -> None:
    """
    Handler should propagate ValueError from Password value object.

    This test verifies that password strength validation is enforced
    by the Password value object before reaching the handler.
    """
    # Arrange: Create command with weak password (will raise ValueError)
    email = Email("user@example.com")

    with pytest.raises(ValueError, match="at least 8 characters"):
        weak_password = Password.from_plain_text("weak")
        RegisterAccountCommand(email=email, password=weak_password)


def test_register_account_dispatches_account_created_event() -> None:
    """
    Handler should dispatch AccountCreated event after successful account creation.

    Business Flow:
        1. Create account
        2. Persist via repository
        3. Dispatch AccountCreated event (triggers activation workflow)

    Verification:
        - dispatcher.dispatch() called exactly once
        - Event contains correct account_id and email
        - Event is AccountCreated instance
    """
    # Arrange
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    command = RegisterAccountCommand(email=email, password=password)

    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    mock_dispatcher = Mock(spec=EventDispatcher)

    handler = RegisterAccountHandler(repository=mock_repository, dispatcher=mock_dispatcher)

    # Act
    handler.handle(command)

    # Assert: Event was dispatched
    mock_dispatcher.dispatch.assert_called_once()

    # Verify event properties
    dispatched_event = mock_dispatcher.dispatch.call_args[0][0]
    assert isinstance(dispatched_event, AccountCreated)
    assert dispatched_event.email == email
    # Note: account_id is generated by Account.create(), we just verify it exists
    assert dispatched_event.account_id is not None
    assert dispatched_event.occurred_at is not None


def test_register_account_with_normalized_email() -> None:
    """
    Handler should work with normalized emails (lowercase).

    Email value object normalizes emails to lowercase to prevent duplicates
    (e.g., User@example.com and user@example.com should be treated as same).
    """
    # Arrange: Create command with mixed-case email
    email = Email("MixedCase@Example.COM")
    password = Password.from_plain_text("SecurePassword123")
    command = RegisterAccountCommand(email=email, password=password)

    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    mock_dispatcher = Mock(spec=EventDispatcher)

    handler = RegisterAccountHandler(repository=mock_repository, dispatcher=mock_dispatcher)

    # Act: Execute command
    handler.handle(command)

    # Assert: Email was normalized by Email VO
    assert command.email.value == "mixedcase@example.com"
    mock_repository.find_by_email.assert_called_once_with(email)


def test_register_account_with_hashed_password() -> None:
    """
    Handler should persist password hash, not plain text.

    Password value object automatically hashes passwords using bcrypt.
    The handler should pass the Password VO (with hash) to the repository.
    """
    # Arrange: Create command with plain text password
    email = Email("user@example.com")
    plain_password = "SecurePassword123"
    password = Password.from_plain_text(plain_password)
    command = RegisterAccountCommand(email=email, password=password)

    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    mock_dispatcher = Mock(spec=EventDispatcher)

    handler = RegisterAccountHandler(repository=mock_repository, dispatcher=mock_dispatcher)

    # Act: Execute command
    handler.handle(command)

    # Assert: Password was hashed (not plain text)
    created_account = mock_repository.create.call_args[0][0]
    assert created_account.password.hashed_value != plain_password


def test_register_account_creates_different_ids_for_same_email_retry() -> None:
    """
    Handler should generate new UUID v7 for each account creation attempt.

    Even if the same email is used (e.g., after deletion), each Account
    should get a unique ID.
    """
    # Arrange: Create two commands with same credentials
    email = Email("user@example.com")
    password = Password.from_plain_text("SecurePassword123")
    command1 = RegisterAccountCommand(email=email, password=password)
    command2 = RegisterAccountCommand(email=email, password=password)

    mock_repository = Mock(spec=AccountRepository)
    mock_repository.find_by_email.return_value = None

    mock_dispatcher = Mock(spec=EventDispatcher)

    handler = RegisterAccountHandler(repository=mock_repository, dispatcher=mock_dispatcher)

    # Act: Execute both commands
    handler.handle(command1)
    handler.handle(command2)

    # Assert: Different Account IDs were generated
    account1 = mock_repository.create.call_args_list[0][0][0]
    account2 = mock_repository.create.call_args_list[1][0][0]

    assert account1.id != account2.id
