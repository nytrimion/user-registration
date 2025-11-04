"""
AccountActivationRepository interface for account activation persistence.

This module defines the repository contract for AccountActivation entity.
The repository provides persistence operations (save, find, delete) for
account activation codes with expiration logic.
"""

from abc import ABC, abstractmethod

from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.value_objects.account_id import AccountId


class AccountActivationRepository(ABC):
    """
    Abstract repository interface for AccountActivation entity.

    This interface defines the contract for persisting and retrieving
    account activation codes. Infrastructure layer provides concrete
    implementations (PostgresAccountActivationRepository, etc.).

    Design Principles:
        - Repository per aggregate root (DDD pattern)
        - Interface in domain layer (no technical dependencies)
        - Concrete implementations in infrastructure layer

    Business Rules Enforced:
        - One active code per account (account_id as primary key)
        - save() performs upsert (replaces existing code for same account)
        - delete() is idempotent (no error if activation doesn't exist)

    Example:
        # Create activation
        activation = AccountActivation.create_for_account(account_id)
        repository.save(activation)

        # Retrieve activation
        found = repository.find_by_account_id(account_id)
        if found and found.is_valid("1234"):
            repository.delete(account_id)  # Remove after successful validation
    """

    @abstractmethod
    def save(self, activation: AccountActivation) -> None:
        """
        Save account activation (upsert by account_id).

        If an activation already exists for this account_id, it will be replaced.
        This enforces the business rule: one active code per account.

        Args:
            activation: AccountActivation entity to persist

        Implementation Notes:
            - PostgreSQL: INSERT ... ON CONFLICT (account_id) DO UPDATE
            - Replace existing code if account_id already exists
            - Store expires_at timestamp for expiration queries

        Example:
            activation = AccountActivation.create_for_account(account_id)
            repository.save(activation)  # First insert

            new_activation = AccountActivation.create_for_account(account_id)
            repository.save(new_activation)  # Replaces previous code (upsert)
        """
        pass

    @abstractmethod
    def find_by_account_id(self, account_id: AccountId) -> AccountActivation | None:
        """
        Find account activation by account ID.

        Args:
            account_id: AccountId to search for

        Returns:
            AccountActivation if found, None otherwise

        Implementation Notes:
            - Return None if no activation exists for this account
            - Return expired activations (caller handles expiration logic)
            - Use bidirectional mapper (DB row → AccountActivation entity)

        Example:
            activation = repository.find_by_account_id(account_id)
            if activation is None:
                print("No activation found for this account")
            elif activation.is_expired():
                print("Activation has expired")
            else:
                print("Activation is still valid")
        """
        pass
