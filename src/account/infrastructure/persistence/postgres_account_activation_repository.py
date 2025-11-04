"""
PostgreSQL implementation of AccountActivationRepository.

This module provides the concrete implementation of the AccountActivationRepository
interface using raw SQL queries with psycopg2. It follows the Repository
pattern from Domain-Driven Design.

Design Decisions:
    - Raw SQL: No ORM magic, explicit queries for clarity
    - Parameterized queries: %s placeholders prevent SQL injection
    - Auto-commit: Repository commits automatically after each operation
    - Value object preservation: Uses mapper to maintain type safety
    - Connection pool: Injected DatabaseConnectionFactory for testability

Architecture:
    - Implements: AccountActivationRepository (domain layer interface)
    - Dependencies: DatabaseConnectionFactory (injected), account_activation_mapper
    - SQL: INSERT ... ON CONFLICT for save(), SELECT for find_by_account_id()
    - Transactions: Each repository method commits automatically

Error Handling:
    - DatabaseError: Propagated to application layer for 500 response
    - Row not found: Returns None (not exception)
    - Foreign key violation: Propagated if account_id doesn't exist

Usage Example:
    ```python
    # In application handler (with injector)
    @inject
    def __init__(self, repository: AccountActivationRepository):
        self._repository = repository

    # Create activation
    activation = AccountActivation.create_for_account(account_id)
    repository.save(activation)  # UPSERT: replaces existing code

    # Find by account_id
    found = repository.find_by_account_id(account_id)
    if found and found.is_valid(user_input):
        # Activation successful
    ```
"""

from injector import inject

from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.repositories.account_activation_repository import (
    AccountActivationRepository,
)
from src.account.domain.value_objects.account_id import AccountId
from src.account.infrastructure.persistence.account_activation_mapper import (
    to_domain,
    to_persistence,
)
from src.shared.infrastructure.database.connection import DatabaseConnectionFactory


class PostgresAccountActivationRepository(AccountActivationRepository):
    """
    PostgreSQL repository implementation for AccountActivation entity.

    Uses raw SQL queries with psycopg2 for explicit database operations.
    Connection pool is injected for testability and resource management.

    Thread Safety:
        - DatabaseConnectionFactory uses ThreadedConnectionPool
        - Safe for concurrent requests in FastAPI
        - Each operation acquires connection from pool

    Transaction Management:
        - Repository methods commit automatically after successful operations
        - Each repository call is an independent transaction
        - Simplifies application layer (no explicit transaction management)

    SQL Queries:
        - UPSERT: Creates or updates activation with account_id, code, timestamps
        - SELECT: Retrieves activation by account_id
        - Constraints: PRIMARY KEY on account_id, FK to account.id

    Dependency Injection:
        - @inject decorator registers for automatic injection
        - DatabaseConnectionFactory provided by InfrastructureModule
        - Can be mocked in unit tests with FakeDatabaseConnectionFactory
    """

    @inject
    def __init__(self, db: DatabaseConnectionFactory) -> None:
        """
        Initialize repository with database connection factory.

        Args:
            db: Injected connection factory (singleton from DI container)
        """
        self._db = db

    def save(self, activation: AccountActivation) -> None:
        """
        Persist account activation in the database (insert or update).

        Uses UPSERT pattern: inserts if account_id doesn't exist, updates otherwise.
        This enforces the business rule: one active code per account.

        Args:
            activation: AccountActivation entity to persist

        Raises:
            psycopg2.ForeignKeyViolation: If account_id doesn't exist in account table
            psycopg2.DatabaseError: If database operation fails

        Transaction:
            - Commits automatically after successful UPSERT
            - Each repository call is an independent transaction
            - UPSERT is atomic (no race condition between INSERT and UPDATE)

        Example:
            >>> activation = AccountActivation.create_for_account(account_id)
            >>> repository.save(activation)  # INSERT (new account_id)
            >>>
            >>> new_activation = AccountActivation.create_for_account(account_id)
            >>> repository.save(new_activation)  # UPDATE (same account_id, new code)
        """
        with self._db.connection() as conn:
            with conn.cursor() as cursor:
                row = to_persistence(activation)
                cursor.execute(
                    """
                    INSERT INTO account_activation (
                        account_id, code, created_at, expires_at
                    )
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (account_id) DO UPDATE SET
                        code = EXCLUDED.code,
                        created_at = EXCLUDED.created_at,
                        expires_at = EXCLUDED.expires_at
                    """,
                    (
                        row["account_id"],
                        row["code"],
                        row["created_at"],
                        row["expires_at"],
                    ),
                )
                # Commit transaction immediately after successful UPSERT
                conn.commit()

    def find_by_account_id(self, account_id: AccountId) -> AccountActivation | None:
        """
        Find account activation by account ID.

        Searches for an activation with the given account_id.
        Returns None if no activation is found.

        Args:
            account_id: AccountId value object to search for

        Returns:
            AccountActivation entity if found, None otherwise

        SQL:
            SELECT account_id, code, created_at, expires_at
            FROM account_activation
            WHERE account_id = %s

        Note:
            - Returns None (not exception) if not found
            - Returns complete AccountActivation entity with all value objects
            - Returns expired activations (caller handles expiration logic)

        Example:
            >>> activation = repository.find_by_account_id(account_id)
            >>> if activation is None:
            ...     print("No activation found")
            >>> elif activation.is_expired():
            ...     print("Activation has expired")
            >>> else:
            ...     print(f"Code: {activation.code.value}")
        """
        with self._db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT account_id, code, created_at, expires_at
                    FROM account_activation
                    WHERE account_id = %s
                    """,
                    (str(account_id.value),),
                )
                row_tuple = cursor.fetchone()

                if row_tuple is None:
                    return None

                # Convert tuple to dictionary for mapper
                # psycopg2 returns tuples by default, not dicts
                column_names = ["account_id", "code", "created_at", "expires_at"]
                row_dict = dict(zip(column_names, row_tuple, strict=False))

                return to_domain(row_dict)
