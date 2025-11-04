"""
Data Transfer Objects (DTOs) for account HTTP endpoints.

These Pydantic models handle request validation and serialization for the HTTP
layer. They are completely separate from domain value objects to maintain clean
architecture boundaries.

Design Decisions:
    - Pydantic v2 for validation (ConfigDict, EmailStr, Field)
    - Primitive types only (str) - no domain objects in DTOs
    - Email/password validation happens in domain layer (Email, Password VOs)
    - DTOs convert to domain objects in controller before handler call

Validation Strategy:
    - Basic format validation in Pydantic (email format, min length)
    - Business rules validation in domain layer (Email VO, Password VO)
    - This separation allows reusing domain logic across different interfaces
"""

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class RegisterAccountRequest(BaseModel):
    """
    Request DTO for POST /accounts endpoint.

    Validates basic input format before passing to domain layer.
    Domain value objects (Email, Password) will apply business rules.

    Attributes:
        email: Email address (format validation by Pydantic EmailStr)
        password: Plain text password (min 8 chars, domain VO enforces complexity)

    Example:
        {
            "email": "user@example.com",
            "password": "SecurePass123!"
        }

    Response:
        HTTP 201 Created (no body)

        The account is created but not yet activated. User must verify their
        email address before the account becomes usable.
    """

    model_config = ConfigDict(
        str_strip_whitespace=True,  # Trim whitespace from strings
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123!",
            }
        },
    )

    email: EmailStr = Field(
        ...,
        description="Email address (must be valid format)",
        examples=["user@example.com"],
    )

    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 characters, complexity enforced by domain)",
        examples=["SecurePass123!"],
    )
