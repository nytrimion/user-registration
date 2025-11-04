"""
Domain exceptions for the Account bounded context.

This module contains domain-specific exceptions that represent business rule
violations or invalid states within the Account aggregate.

Exceptions here are part of the ubiquitous language and should be used by:
- Domain entities (Account, AccountActivation)
- Application services (Use case handlers)
- Infrastructure layer (Repository implementations, HTTP controllers)

Domain exceptions should:
- Express business concepts (not technical errors)
- Be named using domain terminology
- Include context to help users understand the violation

Exception List:
    - EmailAlreadyExistsError: Email uniqueness violation
    - AccountNotFoundError: Account ID does not exist
    - ActivationCodeNotFoundError: No activation code for account
    - ActivationCodeExpiredError: Code expired (>60 seconds)
    - InvalidActivationCodeError: Code value mismatch
"""

from src.account.domain.value_objects.email import Email


class EmailAlreadyExistsError(Exception):
    """
    Raised when attempting to create an account with an email that already exists.

    This exception enforces the business rule that email addresses must be unique
    across all accounts in the system.

    Attributes:
        email: The Email value object that conflicts with an existing account

    Example:
        >>> raise EmailAlreadyExistsError(Email("user@example.com"))
    """

    def __init__(self, email: Email) -> None:
        """
        Initialize the exception with the conflicting email.

        Args:
            email: The Email value object that already exists
        """
        self.email = email
        super().__init__(f"Account with email '{email.value}' already exists")


class AccountNotFoundError(Exception):
    """
    Raised when account with given ID does not exist.

    This occurs when:
    - Attempting to activate non-existent account
    - Loading account for authentication

    Example:
        >>> raise AccountNotFoundError("Account 019... not found")
    """

    pass


class ActivationCodeNotFoundError(Exception):
    """
    Raised when no activation code exists for account.

    This occurs when:
    - Activation code was never created (event handler failed)
    - Activation code was deleted
    - Wrong account ID provided

    Example:
        >>> raise ActivationCodeNotFoundError("No activation code for account 019...")
    """

    pass


class ActivationCodeExpiredError(Exception):
    """
    Raised when activation code expired (>60 seconds since creation).

    Business Rule:
        Activation codes expire 60 seconds after generation.
        User must request new activation code if expired.

    Example:
        >>> raise ActivationCodeExpiredError("Activation code expired (60 second limit)")
    """

    pass


class InvalidActivationCodeError(Exception):
    """
    Raised when activation code value does not match expected code.

    This occurs when:
    - User enters wrong 4-digit code
    - Code format is invalid (validated by ActivationCode VO)

    Example:
        >>> raise InvalidActivationCodeError("Invalid activation code")
    """

    pass
