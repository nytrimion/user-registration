"""
PostgreSQL implementation of AccountRepository.

This module provides the concrete implementation of the AccountRepository
interface using raw SQL queries with psycopg2. It follows the Repository
pattern from Domain-Driven Design.

Design Decisions:
    - Raw SQL: No ORM magic, explicit queries for clarity
    - Parameterized queries: %s placeholders prevent SQL injection
    - Auto-commit: Repository commits automatically after each operation
    - Value object preservation: Uses mapper to maintain type safety
    - Connection pool: Injected DatabaseConnectionFactory for testability

Architecture:
    - Implements: AccountRepository (domain layer interface)
    - Dependencies: DatabaseConnectionFactory (injected), account_mapper
    - SQL: INSERT for create(), SELECT for find_by_email()
    - Transactions: Each repository method commits automatically

Error Handling:
    - IntegrityError (UNIQUE violation): Propagated to application layer
    - DatabaseError: Propagated to controller for 500 response
    - Row not found: Returns None (not exception)

Usage Example:
    ```python
    # In application handler (with injector)
    @inject
    def __init__(self, repository: AccountRepository):
        self._repository = repository

    # Create account
    account = Account.create(email, password)
    repository.create(account)  # Raises IntegrityError if email exists

    # Find by email
    found = repository.find_by_email(Email("user@example.com"))
    if found is None:
        # Account not found
    ```
"""

from injector import inject

from src.account.domain.entities.account import Account
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.value_objects.email import Email
from src.account.infrastructure.persistence.account_mapper import (
    to_domain,
    to_persistence,
)
from src.shared.infrastructure.database.connection import DatabaseConnectionFactory


class PostgresAccountRepository(AccountRepository):
    """
    PostgreSQL repository implementation for Account aggregate.

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
        - INSERT: Creates new account with UUID v7, email, password hash
        - SELECT: Retrieves account by email (case-insensitive via Email VO)
        - Constraints: UNIQUE on email enforced by database

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

    def create(self, account: Account) -> None:
        """
        Persist a new account in the database.

        Inserts account into the account table and commits the transaction
        automatically. Each create() call is an independent transaction.

        Args:
            account: Account entity to persist

        Raises:
            psycopg2.IntegrityError: If email or ID already exists (UNIQUE violation)
            psycopg2.DatabaseError: If database operation fails

        SQL:
            INSERT INTO account (id, email, password_hash, is_activated, created_at, updated_at)
            VALUES (%s, %s, %s, %s, NOW(), NOW())

        Transaction:
            - Commits automatically after successful INSERT
            - Each repository call is an independent transaction
            - For complex workflows requiring multiple operations in one transaction,
              consider implementing Unit of Work pattern

        Example:
            >>> repository.create(account)  # Automatically committed
        """
        with self._db.connection() as conn:
            with conn.cursor() as cursor:
                row = to_persistence(account)
                cursor.execute(
                    """
                    INSERT INTO account (
                        id, email, password_hash, is_activated, created_at, updated_at
                    )
                    VALUES (%s, %s, %s, %s, NOW(), NOW())
                    """,
                    (
                        row["id"],
                        row["email"],
                        row["password_hash"],
                        row["is_activated"],
                    ),
                )
                # Commit transaction immediately after successful INSERT
                # Note: For production systems with complex workflows requiring
                # multiple operations in one transaction (e.g., create account +
                # emit event + save activation code), consider implementing
                # Unit of Work pattern or TransactionManager abstraction.
                conn.commit()

    def find_by_email(self, email: Email) -> Account | None:
        """
        Find account by email address.

        Searches for an account with the given email (case-insensitive).
        Returns None if no account is found.

        Args:
            email: Email value object (already normalized to lowercase)

        Returns:
            Account entity if found, None otherwise

        SQL:
            SELECT id, email, password_hash, is_activated, created_at, updated_at
            FROM account
            WHERE email = %s

        Note:
            - Email comparison is case-insensitive (Email VO normalizes to lowercase)
            - Returns complete Account entity with all value objects
            - Does NOT raise exception if not found (returns None)

        Example:
            >>> account = repository.find_by_email(Email("user@example.com"))
            >>> if account is None:
            ...     print("Account not found")
            >>> else:
            ...     print(f"Found: {account.email}")
        """
        with self._db.connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT id, email, password_hash, is_activated, created_at, updated_at
                    FROM account
                    WHERE email = %s
                    """,
                    (email.value,),
                )
                row_tuple = cursor.fetchone()

                if row_tuple is None:
                    return None

                # Convert tuple to dictionary for mapper
                # psycopg2 returns tuples by default, not dicts
                column_names = [
                    "id",
                    "email",
                    "password_hash",
                    "is_activated",
                    "created_at",
                    "updated_at",
                ]
                row_dict = dict(zip(column_names, row_tuple, strict=False))

                return to_domain(row_dict)
