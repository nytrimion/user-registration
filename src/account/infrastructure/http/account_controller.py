"""
Account HTTP controller.

This module implements HTTP endpoints for account management using FastAPI.
Controllers handle request/response mapping and delegate business logic to
application layer handlers.

Design Decisions:
    - FastAPI APIRouter for modular routing
    - Dependency injection via fastapi-injector (Injected)
    - Domain exceptions mapped to HTTP status codes
    - Controllers are thin: validation → handler → response

Error Handling:
    - EmailAlreadyExistsError → HTTP 409 Conflict
    - ValueError (Email/Password VO) → HTTP 400 Bad Request (handled by Pydantic)
    - Unexpected errors → HTTP 500 Internal Server Error (FastAPI default)

Architecture:
    HTTP Request → DTO validation → Domain VOs → Command → Handler → Repository
"""

from fastapi import APIRouter, HTTPException, Response, status
from fastapi_injector import Injected

from src.account.application.commands.register_account import (
    RegisterAccountCommand,
    RegisterAccountHandler,
)
from src.account.domain.exceptions import EmailAlreadyExistsError
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.infrastructure.http.dtos import RegisterAccountRequest

router = APIRouter(prefix="/accounts", tags=["accounts"])


@router.post(
    "/",
    response_class=Response,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {
            "description": "Domain validation error (Email or Password value object)",
            "content": {
                "application/json": {
                    "example": {"detail": "Password must be at least 8 characters long"}
                }
            },
        },
        409: {
            "description": "Email already registered",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Email address already registered: user@example.com",
                    }
                }
            },
        },
    },
)
def create_account(
    request: RegisterAccountRequest,
    handler: RegisterAccountHandler = Injected(RegisterAccountHandler),
) -> None:
    """
    Create a new user account.

    Registers a new account with email and password. The account is created
    in an inactive state and requires email verification before use.

    Returns: HTTP 201 Created (no response body)

    Business Rules:
    - Email must be unique across all accounts
    - Password must meet complexity requirements (enforced by Password VO)
    - Account created in inactive state (is_activated = False)
    - User must verify email via activation code to use account
    """
    try:
        email = Email(request.email)
        password = Password.from_plain_text(request.password)
        command = RegisterAccountCommand(email=email, password=password)

        handler.handle(command)

    except EmailAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Email address already registered: {e.email.value}",
        ) from e

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
