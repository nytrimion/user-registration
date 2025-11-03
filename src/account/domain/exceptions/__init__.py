"""
Domain exceptions for the Account bounded context.

This module contains domain-specific exceptions that represent business rule
violations or invalid states within the Account aggregate.

Exceptions here are part of the ubiquitous language and should be used by:
- Domain entities (Account)
- Application services (Use case handlers)
- Infrastructure layer (Repository implementations)

Domain exceptions should:
- Express business concepts (not technical errors)
- Be named using domain terminology
- Include context to help users understand the violation
"""

from src.account.domain.value_objects.email import Email


class EmailAlreadyExistsError(Exception):
    """
    Raised when attempting to create an account with an email that already exists.

    This exception enforces the business rule that email addresses must be unique
    across all accounts in the system.

    Attributes:
        email: The Email value object that conflicts with an existing account
    """

    def __init__(self, email: Email) -> None:
        """
        Initialize the exception with the conflicting email.

        Args:
            email: The Email value object that already exists
        """
        self.email = email
        super().__init__(f"Account with email '{email.value}' already exists")
