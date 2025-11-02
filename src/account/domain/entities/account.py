from dataclasses import dataclass, field
from typing import Self

from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password


@dataclass
class Account:
    """
    Account aggregate root.

    Represents a user account with email/password credentials.
    Accounts start pending activation and must be verified via email.

    Construction:
        Use Account.create() for new accounts.
        Direct instantiation is reserved for repository reconstruction.

    Invariants:
        - account_id is immutable (entity identity)
        - email must be unique across all accounts (enforced by repository)
        - password is always hashed
        - is_activated can only transition False → True via activate()
    """

    _account_id: AccountId = field(repr=False)
    _email: Email = field(repr=False)
    _password: Password = field(repr=False)
    _is_activated: bool = field(default=False, repr=False)

    @classmethod
    def create(cls, email: Email, password: Password) -> Self:
        """
        Create a new account pending activation.

        Generates a unique UUID v7 identifier and initializes
        the account with is_activated=False.

        Args:
            email: Validated email address
            password: Hashed password (use Password.from_plain_text())

        Returns:
            New Account instance with generated ID

        Example:
            >>> email = Email("user@example.com")
            >>> password = Password.from_plain_text("SecurePass123")
            >>> account = Account.create(email, password)
            >>> account.is_activated
            False
        """
        return cls(
            _account_id=AccountId.generate(),
            _email=email,
            _password=password,
            _is_activated=False,
        )

    @property
    def account_id(self) -> AccountId:
        return self._account_id

    @property
    def email(self) -> Email:
        return self._email

    @property
    def password(self) -> Password:
        return self._password

    @property
    def is_activated(self) -> bool:
        return self._is_activated

    def activate(self) -> None:
        """
        Activate the account after email verification.

        Business rule: Account can only be activated once.

        Raises:
            ValueError: If account is already activated
        """
        if self._is_activated:
            raise ValueError("Account is already activated")
        self._is_activated = True

    def __eq__(self, other: object) -> bool:
        """
        Entities are compared by ID, not by value.

        Two Account instances are equal if they have the same account_id,
        even if other attributes differ (entity identity pattern).
        """
        if not isinstance(other, Account):
            return NotImplemented
        return self._account_id == other._account_id

    def __hash__(self) -> int:
        return hash(self._account_id)

    def __repr__(self) -> str:
        return (
            f"Account("
            f"account_id={self._account_id!r}, "
            f"email={self._email!r}, "
            f"is_activated={self._is_activated})"
        )
