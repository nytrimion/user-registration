"""
Unit tests for AccountCreatedHandler.

Tests the event handler's orchestration of activation code generation and
email sending workflows. Uses mocks for repositories and services to isolate
business logic.

Test Strategy:
    - Unit tests (no database, no email service)
    - Mock AccountActivationRepository and EmailService
    - Verify workflow orchestration (generate → save → send)
    - Validate email content (link, code, HTML structure)
    - Test error propagation
"""

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from src.account.application.events.account_created_handler import (
    AccountCreatedHandler,
)
from src.account.domain.events.account_created import AccountCreated
from src.account.domain.repositories.account_activation_repository import (
    AccountActivationRepository,
)
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email
from src.shared.application.services.email_service import EmailService


@pytest.fixture
def mock_activation_repository() -> Mock:
    """Provide mock AccountActivationRepository."""
    return Mock(spec=AccountActivationRepository)


@pytest.fixture
def mock_email_service() -> Mock:
    """Provide mock EmailService."""
    return Mock(spec=EmailService)


@pytest.fixture
def handler(mock_activation_repository: Mock, mock_email_service: Mock) -> AccountCreatedHandler:
    """Provide AccountCreatedHandler with mocked dependencies."""
    return AccountCreatedHandler(mock_activation_repository, mock_email_service)


@pytest.fixture
def account_created_event() -> AccountCreated:
    """Provide sample AccountCreated event."""
    return AccountCreated(
        account_id=AccountId.generate(),
        email=Email("user@example.com"),
        occurred_at=datetime.now(UTC),
    )


def test_handle_generates_and_saves_activation_code(
    handler: AccountCreatedHandler,
    mock_activation_repository: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should generate and save activation code.

    Validates:
        - AccountActivation created for account_id
        - Activation saved to repository
        - save() called exactly once
    """
    # Act
    handler.handle(account_created_event)

    # Assert: Activation saved
    assert mock_activation_repository.save.call_count == 1

    # Assert: Activation for correct account_id
    saved_activation = mock_activation_repository.save.call_args[0][0]
    assert saved_activation.account_id == account_created_event.account_id


def test_handle_sends_email_with_activation_link(
    handler: AccountCreatedHandler,
    mock_email_service: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should send email with activation link.

    Validates:
        - Email sent to correct recipient
        - Subject is "Activate your account"
        - Body contains activation link
        - Link format: http://localhost:8000/activate/{id}?code={code}
    """
    # Act
    handler.handle(account_created_event)

    # Assert: Email sent
    assert mock_email_service.send_email.call_count == 1

    # Assert: Email message structure
    email_message = mock_email_service.send_email.call_args[0][0]
    assert email_message.to_email == account_created_event.email
    assert email_message.subject == "Activate your account"

    # Assert: Body contains activation link
    assert "http://localhost:8000/activate/" in email_message.body
    assert str(account_created_event.account_id.value) in email_message.body
    assert "code=" in email_message.body


def test_handle_builds_html_email_body(
    handler: AccountCreatedHandler,
    mock_email_service: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should build HTML email body.

    Validates:
        - HTML structure present
        - Clickable link (anchor tag)
        - Code displayed in body
        - Expiration warning present
    """
    # Act
    handler.handle(account_created_event)

    # Assert: HTML email body
    email_message = mock_email_service.send_email.call_args[0][0]
    body = email_message.body

    assert "<html>" in body
    assert "<a href=" in body
    assert "Activate Account" in body
    assert "60 seconds" in body.lower() or "60s" in body.lower()


def test_handle_includes_code_in_email_body(
    handler: AccountCreatedHandler,
    mock_activation_repository: Mock,
    mock_email_service: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should include activation code in email.

    Validates:
        - 4-digit code visible in email body
        - Code can be manually entered if link doesn't work
    """
    # Act
    handler.handle(account_created_event)

    # Assert: Code in email body
    email_message = mock_email_service.send_email.call_args[0][0]
    body = email_message.body

    # Code is 4 digits, should appear in body
    # Extract code from saved activation
    saved_activation = mock_activation_repository.save.call_args[0][0]
    assert saved_activation.code.code in body


def test_handle_workflow_order(
    handler: AccountCreatedHandler,
    mock_activation_repository: Mock,
    mock_email_service: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should execute workflow in correct order.

    Validates:
        - Activation saved BEFORE email sent
        - Ensures code exists in DB before user receives email
    """
    # Arrange: Track call order
    call_order = []
    mock_activation_repository.save.side_effect = lambda *args: call_order.append("save")
    mock_email_service.send_email.side_effect = lambda *args: call_order.append("email")

    # Act
    handler.handle(account_created_event)

    # Assert: save() before send_email()
    assert call_order == ["save", "email"]


def test_handle_uses_default_from_email(
    handler: AccountCreatedHandler,
    mock_email_service: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should use default from_email.

    Validates:
        - from_email defaults to noreply@example.com (EmailMessage DTO)
    """
    # Act
    handler.handle(account_created_event)

    # Assert: Default from_email
    email_message = mock_email_service.send_email.call_args[0][0]
    assert email_message.from_email.value == "noreply@example.com"


def test_handle_propagates_repository_exception(
    handler: AccountCreatedHandler,
    mock_activation_repository: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should propagate repository exceptions.

    Validates:
        - Repository exceptions bubble up to EventDispatcher
        - Event dispatcher can log and handle errors
    """
    # Arrange: Repository raises exception
    mock_activation_repository.save.side_effect = Exception("Database error")

    # Act & Assert: Exception propagated
    with pytest.raises(Exception, match="Database error"):
        handler.handle(account_created_event)


def test_handle_propagates_email_service_exception(
    handler: AccountCreatedHandler,
    mock_email_service: Mock,
    account_created_event: AccountCreated,
) -> None:
    """
    AccountCreatedHandler.handle() should propagate email service exceptions.

    Validates:
        - Email service exceptions bubble up to EventDispatcher
        - Allows resilience strategies (retry, circuit breaker)
    """
    # Arrange: Email service raises exception
    mock_email_service.send_email.side_effect = Exception("SMTP error")

    # Act & Assert: Exception propagated
    with pytest.raises(Exception, match="SMTP error"):
        handler.handle(account_created_event)


def test_build_email_body_includes_all_elements(
    handler: AccountCreatedHandler,
) -> None:
    """
    _build_email_body() should include all required email elements.

    Validates:
        - Activation link present
        - Code visible
        - Expiration warning
        - Styled button
        - Fallback instructions
    """
    # Arrange
    activation_link = "http://localhost:8000/activate/123?code=1234"
    code = "1234"

    # Act
    body = handler._build_email_body(activation_link, code)

    # Assert: All elements present
    assert activation_link in body
    assert code in body
    assert "60 seconds" in body.lower() or "60s" in body.lower()
    assert "<a href=" in body
    assert "Activate Account" in body or "activate" in body.lower()
    assert "<html>" in body
    assert "</html>" in body
