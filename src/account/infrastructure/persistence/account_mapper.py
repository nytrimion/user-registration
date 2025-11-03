"""
Account entity to database row mapper.

This module provides bidirectional mapping between Account entities
(domain layer) and database rows (infrastructure layer).

Design Principles:
    - Pure functions: No side effects, stateless transformations
    - Explicit VO handling: Preserve type safety by reconstructing value objects
    - Domain-driven: Maps to domain entities, not DTOs
    - Round-trip validation: entity → row → entity preserves data

Architecture:
    - to_persistence(): Domain entity → Database row (dict)
    - to_domain(): Database row (dict) → Domain entity
    - Used by PostgresAccountRepository for INSERT/SELECT operations

Usage Example:
    ```python
    # Saving to database
    account = Account.create(email, password)
    row = to_persistence(account)
    cursor.execute("INSERT INTO account (...) VALUES (%s, ...)", row["id"])

    # Loading from database
    cursor.execute("SELECT * FROM account WHERE email = %s", (email,))
    row = cursor.fetchone()
    account = to_domain(row)
    ```
"""

from datetime import datetime
from uuid import UUID

from src.account.domain.entities.account import Account
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password


def to_persistence(account: Account) -> dict[str, str | bool]:
    """
    Convert Account entity to database row dictionary.

    Extracts primitive values from value objects for database storage.
    The returned dictionary contains all columns needed for INSERT/UPDATE.

    Args:
        account: Account entity from domain layer

    Returns:
        Dictionary with database column names as keys:
            - id: str (UUID converted to string for psycopg2)
            - email: str (from Email.value, normalized lowercase)
            - password_hash: str (from Password.hashed_value, bcrypt hash)
            - is_activated: bool (activation status)

    Note:
        - created_at and updated_at are handled by database (NOW())
        - Password is already hashed by Password value object
        - Email is already normalized by Email value object
        - UUID converted to string for psycopg2 compatibility

    Example:
        >>> account = Account.create(Email("user@example.com"), Password.from_plain_text("pass"))
        >>> row = to_persistence(account)
        >>> row["email"]
        'user@example.com'
        >>> row["is_activated"]
        False
    """
    return {
        "id": str(account.id.value),  # Convert UUID to string for psycopg2
        "email": account.email.value,
        "password_hash": account.password.hashed_value,
        "is_activated": account.is_activated,
    }


def to_domain(row: dict[str, str | UUID | bool | datetime]) -> Account:
    """
    Convert database row to Account entity.

    Reconstructs Account entity from database row by recreating value objects.
    This preserves type safety and domain encapsulation.

    Args:
        row: Database row as dictionary with column names as keys:
            - id: UUID or str (account primary key, converted from string if needed)
            - email: str (normalized email address)
            - password_hash: str (bcrypt hashed password)
            - is_activated: bool (activation status)
            - created_at: datetime (ignored, audit only)
            - updated_at: datetime (ignored, audit only)

    Returns:
        Account: Reconstructed domain entity with value objects

    Note:
        - Uses direct Account() constructor (repository reconstruction pattern)
        - Does NOT use Account.create() (that's for new accounts)
        - Reconstructs value objects from primitive database values
        - Private attributes (_id, _email, etc.) set via constructor
        - Converts string UUID from database to UUID object for AccountId

    Example:
        >>> row = {"id": "019a4ba0-9bf9-71c9-91b2-b51c4e875388", "email": "user@example.com", ...}
        >>> account = to_domain(row)
        >>> isinstance(account.email, Email)
        True
        >>> account.is_activated
        False
    """
    # Convert string UUID from database to UUID object
    account_id = row["id"] if isinstance(row["id"], UUID) else UUID(str(row["id"]))

    return Account(
        _id=AccountId(account_id),
        _email=Email(str(row["email"])),
        _password=Password(str(row["password_hash"])),
        _is_activated=bool(row["is_activated"]),
    )
