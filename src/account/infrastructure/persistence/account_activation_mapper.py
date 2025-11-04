"""
AccountActivation entity to database row mapper.

This module provides bidirectional mapping between AccountActivation entities
(domain layer) and database rows (infrastructure layer).

Design Principles:
    - Pure functions: No side effects, stateless transformations
    - Explicit VO handling: Preserve type safety by reconstructing value objects
    - Domain-driven: Maps to domain entities, not DTOs
    - Round-trip validation: entity → row → entity preserves data

Architecture:
    - to_persistence(): Domain entity → Database row (dict)
    - to_domain(): Database row (dict) → Domain entity
    - Used by PostgresAccountActivationRepository for INSERT/SELECT operations

Usage Example:
    ```python
    # Saving to database
    activation = AccountActivation.create_for_account(account_id)
    row = to_persistence(activation)
    cursor.execute("INSERT INTO account_activation (...) VALUES (%s, ...)", row["account_id"])

    # Loading from database
    cursor.execute("SELECT * FROM account_activation WHERE account_id = %s", (account_id,))
    row = cursor.fetchone()
    activation = to_domain(row)
    ```
"""

from datetime import datetime
from uuid import UUID

from src.account.domain.entities.account_activation import AccountActivation
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.activation_code import ActivationCode


def to_persistence(activation: AccountActivation) -> dict[str, str | datetime]:
    """
    Convert AccountActivation entity to database row dictionary.

    Extracts primitive values from value objects for database storage.
    The returned dictionary contains all columns needed for INSERT/UPDATE.

    Args:
        activation: AccountActivation entity from domain layer

    Returns:
        Dictionary with database column names as keys:
            - account_id: str (UUID converted to string for psycopg2)
            - code: str (from ActivationCode.code, 4-digit string)
            - created_at: datetime (UTC timestamp)
            - expires_at: datetime (UTC timestamp, created_at + 60 seconds)

    Note:
        - AccountId UUID converted to string for psycopg2 compatibility
        - Timestamps are already in UTC (from AccountActivation.create_for_account)
        - Code is already validated by ActivationCode value object

    Example:
        >>> activation = AccountActivation.create_for_account(account_id)
        >>> row = to_persistence(activation)
        >>> row["code"]
        '1234'  # 4-digit code
        >>> isinstance(row["created_at"], datetime)
        True
    """
    return {
        "account_id": str(activation.account_id.value),  # Convert UUID to string
        "code": activation.code.code,
        "created_at": activation.created_at,
        "expires_at": activation.expires_at,
    }


def to_domain(row: dict[str, str | UUID | datetime]) -> AccountActivation:
    """
    Convert database row to AccountActivation entity.

    Reconstructs AccountActivation entity from database row by recreating value objects.
    This preserves type safety and domain encapsulation.

    Args:
        row: Database row as dictionary with column names as keys:
            - account_id: UUID or str (primary key, converted from string if needed)
            - code: str (4-digit activation code)
            - created_at: datetime (UTC timestamp)
            - expires_at: datetime (UTC timestamp)

    Returns:
        AccountActivation: Reconstructed domain entity with value objects

    Note:
        - Uses direct AccountActivation() constructor (repository reconstruction pattern)
        - Does NOT use AccountActivation.create_for_account() (that's for new activations)
        - Reconstructs value objects from primitive database values
        - Private attributes (_account_id, _code, etc.) set via constructor
        - Converts string UUID from database to UUID object for AccountId

    Example:
        >>> row = {"account_id": "019a4ba0-9bf9-71c9-91b2-b51c4e875388", "code": "1234", ...}
        >>> activation = to_domain(row)
        >>> isinstance(activation.code, ActivationCode)
        True
        >>> isinstance(activation.account_id, AccountId)
        True
    """
    # Convert string UUID from database to UUID object
    account_id = (
        row["account_id"] if isinstance(row["account_id"], UUID) else UUID(str(row["account_id"]))
    )

    return AccountActivation(
        _account_id=AccountId(account_id),
        _code=ActivationCode(str(row["code"])),
        _created_at=row["created_at"],  # type: ignore
        _expires_at=row["expires_at"],  # type: ignore
    )
