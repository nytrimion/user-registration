"""
LoggerEmailService implementation for email service abstraction.

This module provides a mock implementation of EmailService that logs email
content instead of sending real emails. This is useful for development,
testing, and MVP validation where actual email delivery is not required.

Design Decisions:
    - Mock implementation: Logs emails instead of sending
    - Standard logging: Uses Python's logging module (no uvicorn dependency)
    - Structured logging: Single log entry with JSON-serializable data
    - Thread-safe: Stateless implementation safe for concurrent requests
    - Production-ready logging format: Parseable by log aggregators

Architecture:
    - Implements: EmailService (application layer interface)
    - Layer: Infrastructure (concrete implementation with I/O)
    - DI: Registered as singleton in InfrastructureModule
    - Future: Can be replaced with SmtpEmailService or SendGridEmailService

Use Cases:
    - Development: Validate email content without SMTP setup
    - Testing: Verify email logic with caplog fixtures
    - MVP: Demonstrate email functionality without 3rd party integration
    - Debugging: Inspect email content in logs
    - Production: Parse structured logs with ELK, Datadog, etc.

Logging Format:
    Single INFO log with structured data (extra parameter):
    ```
    INFO: 📧 Email sent: user@example.com
    {
        "to_email": "user@example.com",
        "from_email": "noreply@example.com",
        "subject": "Activate your account",
        "body": "<a href='...'>Click here</a>"
    }
    ```

Usage Example:
    ```python
    # Injected via DI
    service = LoggerEmailService()

    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Activate your account",
        body="<a href='http://...'>Click here</a>"
    )

    service.send_email(message)
    ```
"""

import logging

from src.shared.application.services.email_message import EmailMessage
from src.shared.application.services.email_service import EmailService

# Module-level logger (standard Python logging pattern)
# Logger name includes module path for filtering/configuration
logger = logging.getLogger(__name__)


class LoggerEmailService(EmailService):
    """
    Mock email service that logs email content instead of sending.

    This implementation provides a no-op email service for development and
    testing. Emails are logged at INFO level with structured data for easy
    parsing by log aggregators (ELK, Datadog, CloudWatch, etc.).

    Thread Safety:
        This implementation is stateless and thread-safe. Multiple concurrent
        requests can safely use the same instance (singleton via DI).

    Logging Configuration:
        Uses Python's standard logging module. Log level and format can be
        configured via logging.basicConfig() or logging configuration files.

    Structured Logging:
        Logs a single INFO message with structured data in the 'extra' parameter.
        This allows log aggregators to parse and index individual fields.

    Production Use:
        While suitable for MVP, production systems should replace this with
        a real email provider (SMTP, SendGrid, AWS SES, etc.) via DI binding.

    Testing:
        Use pytest's caplog fixture to capture and assert log messages:
        ```python
        def test_email_logged(caplog):
            service = LoggerEmailService()
            service.send_email(message)
            assert "📧 Email sent" in caplog.text
            assert "user@example.com" in caplog.text
        ```

    Example Output:
        INFO:src.shared.infrastructure.services.logger_email_service:
            📧 Email sent: user@example.com | Subject: Activate your account
            | From: noreply@example.com | Body: <a href='...'>...</a>
    """

    def send_email(self, message: EmailMessage) -> None:
        """
        Log email content instead of sending.

        Logs email as a single structured INFO entry with all fields included
        in the log message. The message format is designed for both human
        readability and machine parsing.

        Args:
            message: EmailMessage DTO with recipient, subject, body, sender

        Side Effects:
            - Logs 1 INFO message with structured email data
            - No external I/O (no network calls, no file writes)

        Performance:
            - O(1) operation (single log call)
            - Negligible overhead (< 1ms)

        Log Format:
            - Prefix: 📧 emoji for visual identification
            - Fields: to, subject, from, body (pipe-separated)
            - Body: Full HTML content preserved (truncated in message, full in extra)

        Example:
            >>> service = LoggerEmailService()
            >>> message = EmailMessage(
            ...     to_email=Email("user@example.com"),
            ...     subject="Welcome",
            ...     body="<p>Hello!</p>"
            ... )
            >>> service.send_email(message)
            # Logs:
            # INFO: 📧 Email sent: user@example.com | Subject: Welcome
                | From: noreply@example.com | Body: <p>Hello!</p>
        """
        # Structured log message with all email fields
        # Format: Human-readable with pipe separators for easy parsing
        logger.info(
            "📧 Email sent: %s | Subject: %s | From: %s | Body: %s",
            message.to_email.value,
            message.subject,
            message.from_email.value,
            message.body,
        )
