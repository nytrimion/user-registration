"""
RegisterAccount command and handler.

This module implements the user registration use case, which creates a new
account with email uniqueness validation and emits AccountCreated event.

Business Rules:
    - Email addresses must be unique across all accounts
    - Password is hashed before persistence (handled by Password VO)
    - Account is created in inactive state (is_verified = False)
    - AccountCreated event emitted after successful persistence

Command Flow:
    1. Receive RegisterAccountCommand (email, password)
    2. Check if email already exists (business rule validation)
    3. Create Account aggregate via factory method
    4. Persist account via repository
    5. Dispatch AccountCreated event (triggers activation code generation)
"""

from dataclasses import dataclass
from datetime import UTC, datetime

from injector import inject

from src.account.domain.entities.account import Account
from src.account.domain.events.account_created import AccountCreated
from src.account.domain.exceptions import EmailAlreadyExistsError
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.shared.domain.events.event_dispatcher import EventDispatcher


@dataclass(frozen=True)
class RegisterAccountCommand:
    """
    Command to register a new user account.

    Immutable data transfer object representing the user's intention to create
    an account. The command carries only the essential data needed for account
    creation.

    Attributes:
        email: Email value object (validated, normalized)
        password: Password value object (will be hashed)

    Immutability:
        frozen=True prevents modification after instantiation, ensuring
        commands remain valid throughout their lifecycle.
    """

    email: Email
    password: Password


class RegisterAccountHandler:
    """
    Handler for the RegisterAccount command.

    Orchestrates the account creation workflow, enforcing business rules
    and coordinating domain entities with infrastructure persistence.

    This handler is framework-agnostic (no FastAPI, Flask, etc.) and can be:
        - Invoked from HTTP controllers
        - Used in CLI scripts
        - Tested in isolation with mocked dependencies

    Dependencies are injected via the @inject decorator, allowing the handler
    to remain independent of the dependency injection framework.

    Business Logic:
        1. Email uniqueness validation (raises EmailAlreadyExistsError)
        2. Account creation via domain factory method
        3. Persistence via repository abstraction
    """

    @inject
    def __init__(self, repository: AccountRepository, dispatcher: EventDispatcher) -> None:
        """
        Initialize handler with injected dependencies.

        The @inject decorator automatically resolves dependencies based on
        type hints, making the handler independent of FastAPI's request
        lifecycle.

        Args:
            repository: Account repository abstraction (injected)
            dispatcher: Event dispatcher for domain events (injected)
        """
        self._repository = repository
        self._dispatcher = dispatcher

    def handle(self, command: RegisterAccountCommand) -> None:
        """
        Execute the account registration workflow.

        Validates business rules, creates the account aggregate, and persists
        it via the repository.

        Args:
            command: RegisterAccountCommand with email and password

        Raises:
            EmailAlreadyExistsError: If email is already registered
            ValueError: If email or password validation fails (raised by VOs)

        Side Effects:
            - Creates new account record in database
            - Emits AccountCreated domain event (triggers activation workflow)

        Implementation Notes:
            This handler uses a Check-Then-Insert pattern for email uniqueness
            validation. While simpler than Try-Insert-Catch-Constraint, this
            approach has a theoretical race condition window between the check
            and insert operations.

            For production with high concurrency, consider:
            - Database UNIQUE constraint + catch IntegrityError in repository
            - SELECT FOR UPDATE in transaction
            - Optimistic locking with version field

            For this application scope (registration API), the race condition
            risk is acceptable given the low probability and non-critical impact.
        """
        # Business Rule: Email must be unique
        # Note: Race condition possible between find and create (acceptable trade-off)
        existing_account = self._repository.find_by_email(command.email)
        if existing_account is not None:
            raise EmailAlreadyExistsError(command.email)

        account = Account.create(email=command.email, password=command.password)

        self._repository.save(account)

        # Emit AccountCreated domain event
        # Event handler will generate activation code and send email
        self._dispatcher.dispatch(
            AccountCreated(
                account_id=account.id,
                email=account.email,
                occurred_at=datetime.now(UTC),
            )
        )
