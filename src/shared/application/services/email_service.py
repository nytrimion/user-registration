"""
EmailService interface for sending emails via 3rd party providers.

This module defines the contract for email sending operations. Concrete
implementations handle the integration with email providers (SMTP, SendGrid,
AWS SES, etc.) or mock implementations for testing/development.

Design Decisions:
    - Interface in application layer (not domain - this is an infrastructure concern)
    - Abstract base class with single responsibility: send emails
    - Framework-agnostic: no FastAPI/Flask dependencies
    - 3rd party abstraction: implementations delegate to external services

Architecture:
    - Interface: Shared Application Layer (application/services/)
    - Implementations: Infrastructure Layer (infrastructure/services/)
    - Consumed by: Application handlers (AccountCreatedHandler, etc.)
    - DI: Bound via InfrastructureModule (singleton)

Implementations:
    - LoggerEmailService: Logs email content (development/testing)
    - SmtpEmailService: Sends via SMTP server (future)
    - SendGridEmailService: Sends via SendGrid API (future)

Usage Example:
    ```python
    # In application handler
    @inject
    def __init__(self, email_service: EmailService):
        self._email_service = email_service

    def handle(self, event: AccountCreated):
        message = EmailMessage(
            to_email=event.email,
            subject="Activate your account",
            body="<a href='...'>Click here</a>"
        )
        self._email_service.send_email(message)
    ```
"""

from abc import ABC, abstractmethod

from src.shared.application.services.email_message import EmailMessage


class EmailService(ABC):
    """
    Abstract service for sending emails via 3rd party providers.

    This interface abstracts email delivery, allowing different implementations
    for different environments or providers. The service is stateless and
    thread-safe.

    Design Principles:
        - Single Responsibility: Only sends emails (no templating, no queuing)
        - Dependency Inversion: Application depends on interface, not implementation
        - Open/Closed: New providers added via new implementations (no interface change)

    Implementations:
        Concrete implementations reside in infrastructure layer and handle:
        - Connection to email provider (SMTP, API, etc.)
        - Error handling and retries
        - Logging and monitoring
        - Rate limiting (if needed)

    Thread Safety:
        Implementations must be thread-safe for concurrent use in FastAPI.
        Stateless implementations (like LoggerEmailService) are inherently safe.

    Error Handling:
        Implementations should raise exceptions on failure (EmailSendError, etc.)
        to allow callers to handle transient failures (retry logic, etc.).

    Example:
        >>> service = LoggerEmailService()
        >>> message = EmailMessage(
        ...     to_email=Email("user@example.com"),
        ...     subject="Welcome",
        ...     body="<p>Hello!</p>"
        ... )
        >>> service.send_email(message)  # Logs email content
    """

    @abstractmethod
    def send_email(self, message: EmailMessage) -> None:
        """
        Send email via 3rd party provider (or mock implementation).

        This method is the single entry point for all email sending operations.
        Implementations handle the actual delivery (SMTP, API call, logging, etc.).

        Args:
            message: EmailMessage DTO with recipient, subject, body, sender

        Raises:
            Exception: Implementation-specific exceptions on failure
                (EmailSendError, SmtpError, ApiError, etc.)

        Side Effects:
            - External API call to email provider
            - Logs email delivery attempt/success/failure
            - May trigger async operations (queue, retry logic)

        Implementation Notes:
            - Validate message fields (non-empty subject, body)
            - Handle transient failures (retries, exponential backoff)
            - Log all operations for observability
            - Support both plain text and HTML body

        Example:
            ```python
            # LoggerEmailService implementation
            def send_email(self, message: EmailMessage) -> None:
                logger.info(f"📧 Email to {message.to_email.value}")
                logger.info(f"Subject: {message.subject}")
                logger.info(f"Body:\\n{message.body}")

            # SmtpEmailService implementation (future)
            def send_email(self, message: EmailMessage) -> None:
                with smtplib.SMTP(host, port) as server:
                    server.send_message(...)
            ```
        """
        pass
