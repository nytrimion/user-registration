"""
EmailMessage DTO for email sending abstraction.

This module defines the data transfer object used to send emails via
EmailService. It encapsulates all necessary information for email delivery
and provides a default sender address.

Design Decisions:
    - Immutable DTO: @dataclass(frozen=True) prevents modification
    - Value Object composition: Uses Email VO for type safety
    - Default sender: noreply@example.com for convenience
    - HTML support: body accepts plain text or HTML content
    - Application layer: DTO used by application services (not domain)

Architecture:
    - Used by: AccountCreatedHandler, other notification handlers
    - Consumed by: EmailService implementations (LoggerEmailService, etc.)
    - Layer: Shared Application (cross-cutting concern)

Usage Example:
    ```python
    # Simple notification
    message = EmailMessage(
        to_email=Email("user@example.com"),
        subject="Account Created",
        body="<p>Welcome!</p>"
    )

    # Custom sender
    message = EmailMessage(
        to_email=Email("user@example.com"),
        from_email=Email("support@example.com"),
        subject="Account Created",
        body="<p>Welcome!</p>"
    )
    ```
"""

from dataclasses import dataclass

from src.account.domain.value_objects.email import Email


@dataclass(frozen=True)
class EmailMessage:
    """
    Immutable DTO for email sending operations.

    Encapsulates all information needed to send an email via EmailService.
    The DTO is framework-agnostic and can be used with any email provider
    (SMTP, SendGrid, Mailgun, etc.).

    Attributes:
        to_email: Recipient email address (Email VO for validation)
        subject: Email subject line
        body: Email body content (supports HTML or plain text)
        from_email: Sender email address (default: noreply@example.com)

    Immutability:
        frozen=True ensures the message cannot be modified after creation,
        preventing accidental mutations during async processing or retries.

    Default Sender:
        from_email defaults to noreply@example.com for convenience.
        This can be overridden per message or configured via dependency injection.

    HTML Support:
        The body field accepts both plain text and HTML content.
        EmailService implementations should handle both formats appropriately.

    Example:
        >>> message = EmailMessage(
        ...     to_email=Email("user@example.com"),
        ...     subject="Activate your account",
        ...     body="<a href='...'>Click here</a>"
        ... )
        >>> message.from_email.value
        'noreply@example.com'
    """

    to_email: Email
    subject: str
    body: str
    from_email: Email = Email("noreply@example.com")
