from abc import ABC, abstractmethod

from src.account.domain.entities.account import Account
from src.account.domain.value_objects.email import Email


class AccountRepository(ABC):
    """
    Repository contract for Account aggregate persistence.

    This interface defines the persistence operations for the Account
    aggregate root. It belongs to the domain layer and must remain
    independent of technical implementation details (no database drivers,
    ORMs, or infrastructure concerns).

    Concrete implementations reside in the infrastructure layer.

    Domain-Driven Design Principles:
        - Repository per aggregate root (Account is the aggregate root)
        - Returns domain entities, not DTOs or database records
        - Accepts value objects as parameters (not primitive types)
        - Explicit methods for distinct operations (create, update, delete)
    """

    @abstractmethod
    def create(self, account: Account) -> None:
        """
        Persist a new account in the data store.

        Creates a new account record. The account must not already exist
        (uniqueness constraints must be enforced by the implementation).

        Args:
            account: The Account aggregate to persist

        Raises:
            Exception: If account with same email already exists
            Exception: If account with same account_id already exists

        Business Rules:
            - Email uniqueness must be enforced
            - Account ID uniqueness must be enforced
            - Password is already hashed by Password value object

        Implementation Notes:
            - Use account.id as primary key
            - Store password hash as-is (already processed)
            - Enforce database constraints (UNIQUE on email)
        """
        pass

    @abstractmethod
    def find_by_email(self, email: Email) -> Account | None:
        """
        Find an account by its email address.

        Searches for an existing account with the given email.
        Returns None if no account is found.

        Args:
            email: The Email value object to search for

        Returns:
            Account if found, None otherwise

        Business Rules:
            - Email comparison must be case-insensitive (normalized by Email VO)
            - Returns complete Account aggregate with all properties

        Implementation Notes:
            - Use exact match on normalized email (Email VO handles normalization)
            - Reconstruct Account entity with all value objects
            - Return None (not exception) if not found
        """
        pass
