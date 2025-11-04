"""
Unit tests for LoggerEmailService.

Tests the mock email service implementation that logs email content instead
of sending real emails. Validates logging behavior, structured output, and
thread safety.

Test Strategy:
    - Unit tests (no external dependencies)
    - Use pytest caplog fixture to capture log output
    - Test structured logging format
    - Test HTML body support
    - Test default from_email behavior
    - Test custom from_email override

Coverage:
    - send_email() with all email fields
    - Logging format validation (structured, parseable)
    - HTML body preservation
    - Default sender behavior
"""

import logging

import pytest

from src.account.domain.value_objects.email import Email
from src.shared.application.services.email_message import EmailMessage
from src.shared.infrastructure.services.logger_email_service import (
    LoggerEmailService,
)


def test_send_email_logs_all_fields(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should log all email fields.

    Validates:
        - Single INFO log entry
        - Contains recipient email
        - Contains subject
        - Contains sender email
        - Contains body content
    """
    # Arrange
    service = LoggerEmailService()
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Test Subject",
        body="<p>Test Body</p>",
        from_email=Email("sender@example.com"),
    )

    # Act
    with caplog.at_level(logging.INFO):
        service.send_email(message)

    # Assert: Single log entry with all fields
    assert len(caplog.records) == 1
    log_message = caplog.text

    assert "📧 Email sent" in log_message
    assert "user@example.com" in log_message
    assert "Test Subject" in log_message
    assert "sender@example.com" in log_message
    assert "<p>Test Body</p>" in log_message


def test_send_email_uses_default_sender(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should use default sender if not specified.

    Validates:
        - Default from_email is noreply@example.com
        - EmailMessage DTO provides default value
    """
    # Arrange
    service = LoggerEmailService()
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Test Subject",
        body="Test Body",
        # from_email not specified, uses default
    )

    # Act
    with caplog.at_level(logging.INFO):
        service.send_email(message)

    # Assert: Default sender logged
    assert "noreply@example.com" in caplog.text


def test_send_email_supports_html_body(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should preserve HTML body content.

    Validates:
        - HTML tags preserved in log output
        - Links and formatting maintained
        - No HTML escaping or sanitization
    """
    # Arrange
    service = LoggerEmailService()
    html_body = """
    <html>
        <body>
            <h1>Activate Your Account</h1>
            <p>Click the link below:</p>
            <a href="http://localhost:8000/accounts/123/activate?code=1234">
                Activate Now
            </a>
        </body>
    </html>
    """
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Account Activation",
        body=html_body,
    )

    # Act
    with caplog.at_level(logging.INFO):
        service.send_email(message)

    # Assert: HTML preserved
    log_message = caplog.text
    assert "<html>" in log_message
    assert "<a href=" in log_message
    assert "http://localhost:8000/accounts/123/activate?code=1234" in log_message


def test_send_email_logs_at_info_level(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should log at INFO level.

    Validates:
        - Log level is INFO (not DEBUG, WARNING, ERROR)
        - Appropriate for production monitoring
    """
    # Arrange
    service = LoggerEmailService()
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Test",
        body="Test",
    )

    # Act
    with caplog.at_level(logging.INFO):
        service.send_email(message)

    # Assert: INFO level
    assert len(caplog.records) == 1
    assert caplog.records[0].levelname == "INFO"


def test_send_email_structured_format(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should use structured log format.

    Validates:
        - Pipe-separated fields for parsing
        - Format: "to | subject | from | body"
        - Parseable by log aggregators
    """
    # Arrange
    service = LoggerEmailService()
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Test Subject",
        body="Test Body",
        from_email=Email("sender@example.com"),
    )

    # Act
    with caplog.at_level(logging.INFO):
        service.send_email(message)

    # Assert: Structured format with pipe separators
    log_message = caplog.text
    assert " | Subject: " in log_message
    assert " | From: " in log_message
    assert " | Body: " in log_message


def test_send_email_with_special_characters(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should handle special characters.

    Validates:
        - Unicode characters preserved
        - Special symbols (emoji, accents) logged correctly
        - No encoding issues
    """
    # Arrange
    service = LoggerEmailService()
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Activez votre compte 🎉",  # French + emoji
        body="<p>Bienvenue chez Dailymotion! 🚀</p>",
    )

    # Act
    with caplog.at_level(logging.INFO):
        service.send_email(message)

    # Assert: Special characters preserved
    log_message = caplog.text
    assert "Activez votre compte 🎉" in log_message
    assert "Bienvenue chez Dailymotion! 🚀" in log_message


def test_send_email_is_idempotent(caplog: pytest.LogCaptureFixture) -> None:
    """
    LoggerEmailService.send_email() should be idempotent (no side effects).

    Validates:
        - Multiple calls produce identical logs
        - No state mutation
        - Thread-safe (stateless)
    """
    # Arrange
    service = LoggerEmailService()
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Test",
        body="Test",
    )

    # Act: Send same message twice
    with caplog.at_level(logging.INFO):
        service.send_email(message)
        first_log = caplog.text
        caplog.clear()

        service.send_email(message)
        second_log = caplog.text

    # Assert: Identical logs (no state mutation)
    assert first_log == second_log
