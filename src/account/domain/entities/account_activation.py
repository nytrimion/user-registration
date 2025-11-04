"""
AccountActivation entity for account activation workflow.

This module defines the AccountActivation entity that manages the lifecycle
of account activation codes, including generation, validation, and expiration.
"""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.activation_code import ActivationCode


@dataclass
class AccountActivation:
    """
    Entity representing an account activation with expiration logic.

    AccountActivation is an entity identified by account_id (composite primary key).
    It encapsulates a 4-digit activation code with 60-second expiration logic.

    Identity:
        account_id: AccountId (composite primary key - enforces one code per account)

    Attributes:
        _account_id: Unique identifier of the account (private)
        _code: 4-digit activation code (private)
        _created_at: UTC timestamp when activation was created (private)
        _expires_at: UTC timestamp when activation expires (private)

    Business Rules:
        - One active code per account (enforced by account_id as PK)
        - Code expires 60 seconds after creation
        - Expired codes are invalid (even if code matches)

    Example:
        # Create activation for account
        activation = AccountActivation.create_for_account(account_id)

        # Validate user input
        if activation.is_valid("1234"):
            print("Code is valid and not expired!")

        # Check expiration
        if activation.is_expired():
            print("Code has expired")
    """

    _account_id: AccountId
    _code: ActivationCode
    _created_at: datetime
    _expires_at: datetime

    EXPIRATION_SECONDS: int = 60

    @classmethod
    def create_for_account(cls, account_id: AccountId) -> "AccountActivation":
        """
        Create new activation for given account.

        Factory method that generates a random 4-digit code and sets
        expiration to 60 seconds from creation time.

        Args:
            account_id: AccountId for which to create activation

        Returns:
            AccountActivation: New instance with generated code and expiration

        Example:
            account_id = AccountId.from_string("0192a4e3-7890-7bcd-8000-123456789abc")
            activation = AccountActivation.create_for_account(account_id)
        """
        code = ActivationCode.generate()
        created_at = datetime.now(UTC)
        expires_at = created_at + timedelta(seconds=cls.EXPIRATION_SECONDS)

        return cls(
            _account_id=account_id,
            _code=code,
            _created_at=created_at,
            _expires_at=expires_at,
        )

    @property
    def account_id(self) -> AccountId:
        """Get account identifier."""
        return self._account_id

    @property
    def code(self) -> ActivationCode:
        """Get activation code."""
        return self._code

    @property
    def created_at(self) -> datetime:
        """Get creation timestamp (UTC)."""
        return self._created_at

    @property
    def expires_at(self) -> datetime:
        """Get expiration timestamp (UTC)."""
        return self._expires_at

    def is_expired(self) -> bool:
        """
        Check if activation has expired.

        Returns:
            bool: True if current time > expires_at, False otherwise

        Example:
            activation = AccountActivation.create_for_account(account_id)
            time.sleep(61)
            activation.is_expired()  # True
        """
        return datetime.now(UTC) > self._expires_at

    def is_valid(self, input_code: str) -> bool:
        """
        Validate activation code and expiration.

        Combined validation: code must match AND activation must not be expired.

        Args:
            input_code: User-provided code to validate

        Returns:
            bool: True if code matches and not expired, False otherwise

        Example:
            activation = AccountActivation.create_for_account(account_id)

            # Valid: correct code + not expired
            activation.is_valid("1234")  # True (if code matches)

            # Invalid: wrong code
            activation.is_valid("0000")  # False

            # Invalid: correct code but expired
            time.sleep(61)
            activation.is_valid("1234")  # False (expired)
        """
        return self._code.matches(input_code) and not self.is_expired()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AccountActivation):
            return NotImplemented
        return self._account_id == other._account_id

    def __hash__(self) -> int:
        return hash(self._account_id)
