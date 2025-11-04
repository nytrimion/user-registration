"""
AccountCreatedHandler event handler.

This module implements the event handler that reacts to AccountCreated events
by generating activation codes and sending activation emails to users.

Business Flow:
    1. Listen for AccountCreated event (emitted by RegisterAccountHandler)
    2. Generate 4-digit activation code with 60-second expiration
    3. Persist activation code to database (AccountActivationRepository)
    4. Build activation link with AccountId and code
    5. Construct HTML email with clickable activation link
    6. Send email via EmailService (LoggerEmailService for MVP)

Architecture:
    - Event Handler: Reacts to domain events (decoupled from command handler)
    - Application Layer: Orchestrates domain entities and infrastructure services
    - Dependency Injection: Receives repositories and services via @inject
    - Synchronous MVP: Executes immediately in same thread (documented trade-off)

Design Decisions:
    - Base URL hardcoded: http://localhost:8000 (MVP simplification)
    - HTML email: Supports clickable link for user-friendly activation
    - Email subject: "Activate your account" (configurable via EmailMessage)
    - From email: noreply@example.com (default in EmailMessage DTO)

Usage Example:
    ```python
    # Registered in EventDispatcher
    dispatcher.register(AccountCreated, AccountCreatedHandler)

    # Triggered automatically when event dispatched
    event = AccountCreated(account_id=..., email=..., occurred_at=...)
    dispatcher.dispatch(event)  # Calls handler.handle(event)
    ```
"""

from injector import inject

from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.events.account_created import AccountCreated
from src.account.domain.repositories.account_activation_repository import (
    AccountActivationRepository,
)
from src.shared.application.services.email_message import EmailMessage
from src.shared.application.services.email_service import EmailService

# Base URL for activation links (hardcoded for MVP)
# TODO: Move to environment variable or Config service for production
BASE_URL = "http://localhost:8000"


class AccountCreatedHandler:
    """
    Event handler for AccountCreated domain event.

    Orchestrates the account activation workflow by generating activation codes
    and sending activation emails. This handler is invoked automatically by the
    EventDispatcher when an AccountCreated event is dispatched.

    Dependencies:
        - AccountActivationRepository: Persists activation codes to database
        - EmailService: Sends activation emails (LoggerEmailService for MVP)

    Thread Safety:
        This handler is stateless and thread-safe. Repository and EmailService
        are singletons managed by dependency injection.

    Synchronous Execution:
        For MVP, this handler executes synchronously in the same thread as the
        RegisterAccountHandler. HTTP response blocks until email is sent.

        Future Evolution: Replace with async execution (queue + background worker)
        to decouple account creation from email delivery.

    Example:
        >>> # Injected automatically via DI
        >>> handler = AccountCreatedHandler(activation_repo, email_service)
        >>>
        >>> # Called automatically by EventDispatcher
        >>> event = AccountCreated(account_id, email, occurred_at)
        >>> handler.handle(event)
        # Output:
        # - Activation code saved to database
        # - Email logged with activation link
    """

    @inject
    def __init__(
        self,
        activation_repository: AccountActivationRepository,
        email_service: EmailService,
    ) -> None:
        """
        Initialize handler with injected dependencies.

        The @inject decorator automatically resolves dependencies based on
        type hints, allowing the handler to work outside HTTP request context.

        Args:
            activation_repository: Repository for persisting activation codes
            email_service: Service for sending emails (LoggerEmailService)
        """
        self._activation_repository = activation_repository
        self._email_service = email_service

    def handle(self, event: AccountCreated) -> None:
        """
        Handle AccountCreated event by generating code and sending email.

        Workflow:
            1. Generate activation code (AccountActivation.create_for_account)
            2. Persist code to database (activation_repository.save)
            3. Build activation link (BASE_URL + accountId + code)
            4. Construct HTML email body with clickable link
            5. Send email via EmailService

        Args:
            event: AccountCreated domain event with account_id, email, occurred_at

        Side Effects:
            - Inserts activation code in account_activation table
            - Logs email content (MVP) or sends via SMTP (production)

        Business Rules:
            - Code expires 60 seconds after generation
            - One code per account (UPSERT in repository)
            - Email contains clickable link to activation page

        Error Handling:
            Exceptions propagate to EventDispatcher, which logs and continues.
            Account creation succeeds even if email fails (resilience pattern).

        Example:
            >>> event = AccountCreated(
            ...     account_id=AccountId("019..."),
            ...     email=Email("user@example.com"),
            ...     occurred_at=datetime.now(UTC)
            ... )
            >>> handler.handle(event)
            # Database: INSERT INTO account_activation (account_id, code, ...)
            # Log: 📧 Email sent: user@example.com | Subject: Activate your account | ...
        """
        activation = AccountActivation.create_for_account(event.account_id)

        self._activation_repository.save(activation)

        activation_link = (
            f"{BASE_URL}/activate/{event.account_id.value}?code={activation.code.code}"
        )
        email_body = self._build_email_body(activation_link, activation.code.code)

        message = EmailMessage(
            to_email=event.email,
            subject="Activate your account",
            body=email_body,
            # from_email uses default: noreply@example.com
        )

        self._email_service.send_email(message)

    def _build_email_body(self, activation_link: str, code: str) -> str:
        """
        Build HTML email body with activation link and code.

        Creates a simple HTML email with:
        - Greeting and instructions
        - Clickable activation link
        - Plain text code (for manual entry if needed)
        - Expiration warning (60 seconds)

        Args:
            activation_link: Full URL to activation page
            code: 4-digit activation code

        Returns:
            str: HTML email body

        Example:
            >>> body = handler._build_email_body("http://...", "1234")
            >>> "Click the link below to activate" in body
            True
            >>> "1234" in body
            True
        """
        # Ruff E501: HTML lines split for readability
        button_style = (
            "background-color: #4CAF50; color: white; padding: 12px 24px; "
            "text-decoration: none; border-radius: 4px; display: inline-block;"
        )
        code_style = "font-size: 24px; color: #4CAF50;"

        return f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2 style="color: #4CAF50;">Welcome! Activate your account</h2>
                <p>
                    Thank you for registering.
                    To complete your registration, please activate your account.
                </p>

                <p style="margin: 20px 0;">
                    <a href="{activation_link}" style="{button_style}">
                        Activate Account
                    </a>
                </p>

                <p>
                    Or use this activation code:
                    <strong style="{code_style}">{code}</strong>
                </p>

                <p style="color: #666; font-size: 12px;">
                    ⚠️ This code expires in 60 seconds.
                    If it expires, you'll need to request a new one.
                </p>

                <hr style="border: none; border-top: 1px solid #eee; margin: 20px 0;">
                <p style="color: #999; font-size: 11px;">
                    If you didn't create an account, please ignore this email.
                </p>
            </body>
        </html>
        """
