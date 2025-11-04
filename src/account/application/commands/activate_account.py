"""
ActivateAccount use case.

This module implements the account activation workflow. It validates the
activation code, checks expiration, and marks the account as active.

Business Flow:
    1. Load account by ID (AccountRepository.find_by_id)
    2. Load activation code (AccountActivationRepository.find_by_account_id)
    3. Validate code exists
    4. Validate code not expired (60 seconds)
    5. Validate code value matches
    6. Mark account as active (account.activate())
    7. Persist changes (AccountRepository.save)

Architecture:
    - Command Handler: Application layer orchestration
    - Dependency Injection: Repositories via @inject
    - Domain Exceptions: Business rule violations
    - Idempotent Operation: No error if already active

Design Decision:
    - Command and Handler in same file (pragmatic CQRS for <10 use cases)
    - ActivationCode as Value Object (not raw string) for type safety
    - Repository returns None (not exception) for "not found"
    - Handler raises domain exceptions for business rule violations

Usage Example:
    ```python
    # Injected via DI in controller
    handler = ActivateAccountHandler(account_repo, activation_repo)

    command = ActivateAccountCommand(
        account_id=AccountId(uuid),
        code=ActivationCode("1234")
    )

    handler.handle(command)  # Raises domain exceptions on failure
    ```
"""

from dataclasses import dataclass

from injector import inject

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
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.activation_code import ActivationCode


@dataclass(frozen=True)
class ActivateAccountCommand:
    """
    Command to activate an account with verification code.

    This DTO encapsulates the input parameters for account activation.
    It is immutable (frozen dataclass) to ensure thread safety and prevent
    accidental modification.

    Attributes:
        account_id: ID of account to activate (UUID v7)
        code: 4-digit activation code from email (Value Object)

    Example:
        >>> command = ActivateAccountCommand(
        ...     account_id=AccountId(UUID("019...")),
        ...     code=ActivationCode("1234")
        ... )
    """

    account_id: AccountId
    code: ActivationCode


class ActivateAccountHandler:
    """
    Use case handler for account activation.

    Validates activation code and marks account as active. This handler
    orchestrates the activation workflow by coordinating repositories and
    enforcing business rules.

    Business Rules:
        - Account must exist
        - Activation code must exist for account
        - Code must not be expired (60 seconds since creation)
        - Code value must match input
        - Account marked as active (idempotent - no error if already active)

    Dependencies:
        - AccountRepository: Load and persist account state
        - AccountActivationRepository: Load activation codes

    Error Handling:
        Raises domain exceptions for business rule violations:
        - AccountNotFoundError: Account ID not found
        - ActivationCodeNotFoundError: No code exists for account
        - ActivationCodeExpiredError: Code expired (>60s)
        - InvalidActivationCodeError: Code value mismatch

    Thread Safety:
        Stateless handler, thread-safe. Repositories are singletons.

    Idempotence:
        Calling activate() on already-active account is safe (no-op).
        This allows retrying activation without error.

    Example:
        >>> command = ActivateAccountCommand(account_id, code)
        >>> handler.handle(command)
        # Account marked as active in database
    """

    @inject
    def __init__(
        self,
        account_repository: AccountRepository,
        activation_repository: AccountActivationRepository,
    ) -> None:
        """
        Initialize handler with injected dependencies.

        The @inject decorator automatically resolves dependencies based on
        type hints, allowing the handler to work outside HTTP request context.

        Args:
            account_repository: Repository for account persistence
            activation_repository: Repository for activation codes
        """
        self._account_repository = account_repository
        self._activation_repository = activation_repository

    def handle(self, command: ActivateAccountCommand) -> None:
        """
        Handle account activation command.

        Validates activation code and marks account as active.

        Args:
            command: ActivateAccountCommand with account_id and code

        Raises:
            AccountNotFoundError: Account does not exist
            ActivationCodeNotFoundError: No activation code for account
            ActivationCodeExpiredError: Code expired (>60 seconds)
            InvalidActivationCodeError: Code value does not match

        Side Effects:
            - Updates account.is_activated to True in database
            - Idempotent: No error if account already active

        Validation Order:
            1. Account exists (fail fast if account not found)
            2. Activation code exists
            3. Code not expired (check time before value)
            4. Code value matches
            5. Activate account (domain entity method)
            6. Persist changes

        Example:
            >>> command = ActivateAccountCommand(
            ...     account_id=AccountId(uuid),
            ...     code=ActivationCode("1234")
            ... )
            >>> handler.handle(command)
            # Database: UPDATE account SET is_activated = TRUE WHERE id = ...
        """
        account = self._account_repository.find_by_id(command.account_id)
        if not account:
            raise AccountNotFoundError(f"Account {command.account_id.value} not found")

        activation = self._activation_repository.find_by_account_id(command.account_id)
        if not activation:
            raise ActivationCodeNotFoundError(
                f"No activation code found for account {command.account_id.value}"
            )

        if activation.is_expired():
            raise ActivationCodeExpiredError("Activation code expired (60 second limit)")

        if activation.code != command.code:
            raise InvalidActivationCodeError("Invalid activation code")

        account.activate()

        self._account_repository.save(account)
