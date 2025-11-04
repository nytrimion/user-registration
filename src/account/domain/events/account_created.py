"""
AccountCreated domain event.

Emitted after successful account persistence. Triggers asynchronous workflows
like activation code generation and email sending.
"""

from dataclasses import dataclass
from datetime import datetime

from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email


@dataclass(frozen=True)
class AccountCreated:
    """
    Domain event representing successful account creation.

    This event is emitted by RegisterAccountHandler after persisting
    the account in the database. Event handlers can react to this event
    to trigger side effects (e.g., send activation email).

    Attributes:
        account_id: Unique identifier of the created account (UUID v7)
        email: Email address of the account (value object)
        occurred_at: UTC timestamp when the event occurred

    Immutability:
        frozen=True ensures event data cannot be modified after creation.
        This guarantees event integrity throughout the system.

    Example:
        event = AccountCreated(
            account_id=AccountId("0192a4e3-7890-7bcd-8000-123456789abc"),
            email=Email("user@example.com"),
            occurred_at=datetime.now(UTC)
        )

    Design Notes:
        - Uses value objects (AccountId, Email) instead of primitives
        - No business logic (pure data carrier)
        - Past tense naming (AccountCreated, not CreateAccount)
        - No infrastructure dependencies (pure domain)
    """

    account_id: AccountId
    email: Email
    occurred_at: datetime
