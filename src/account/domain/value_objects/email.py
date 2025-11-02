from dataclasses import dataclass

from email_validator import EmailNotValidError, validate_email


@dataclass(frozen=True)
class Email:
    """
    Email value object with strict validation.

    Immutable representation of a valid email address.
    Uses email-validator library for RFC 5322 compliance.

    Attributes:
        value: The normalized email address (lowercase)

    Raises:
        ValueError: If email format is invalid or empty
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("Email cannot be empty")

        try:
            validated = validate_email(self.value, check_deliverability=False)

            # Normalize to full lowercase to prevent duplicate accounts
            # (e.g., User@example.com and user@example.com should be the same)
            # Using object.__setattr__ as workaround for frozen dataclass
            object.__setattr__(self, "value", validated.normalized.lower())

        except EmailNotValidError as e:
            raise ValueError(f"Invalid email: {str(e)}") from e

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"Email(value='{self.value}')"
