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
    - Basic Auth for activation endpoint (configurable via env vars)

Error Handling:
    - EmailAlreadyExistsError → HTTP 409 Conflict
    - AccountNotFoundError, ActivationCodeNotFoundError → HTTP 404 Not Found
    - ActivationCodeExpiredError, InvalidActivationCodeError → HTTP 400 Bad Request
    - ValueError (VO validation) → HTTP 422 Unprocessable Entity
    - Invalid Basic Auth → HTTP 401 Unauthorized
    - Unexpected errors → HTTP 500 Internal Server Error (FastAPI default)

Basic Auth Configuration:
    - Default credentials: username="api", password="secret"
    - Override via environment variables (API_USERNAME, API_PASSWORD)
    - Validation function: src.shared.infrastructure.http.auth.validate_api_credentials

Architecture:
    HTTP Request → DTO validation → Domain VOs → Command → Handler → Repository
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi_injector import Injected

from src.account.application.commands.activate_account import (
    ActivateAccountCommand,
    ActivateAccountHandler,
)
from src.account.application.commands.register_account import (
    RegisterAccountCommand,
    RegisterAccountHandler,
)
from src.account.domain.exceptions import (
    AccountNotFoundError,
    ActivationCodeExpiredError,
    ActivationCodeNotFoundError,
    EmailAlreadyExistsError,
    InvalidActivationCodeError,
)
from src.account.domain.value_objects.account_id import AccountId
from src.account.domain.value_objects.activation_code import ActivationCode
from src.account.domain.value_objects.email import Email
from src.account.domain.value_objects.password import Password
from src.account.infrastructure.http.dtos import (
    ActivateAccountRequest,
    RegisterAccountRequest,
)
from src.shared.infrastructure.http.auth import validate_api_credentials

router = APIRouter(prefix="/accounts", tags=["accounts"])
security = HTTPBasic()


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"description": "Account created (no body)"},
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
    response_class=Response,
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


@router.post(
    "/{account_id}/activate",
    status_code=status.HTTP_200_OK,
    response_class=Response,
    responses={
        200: {"description": "Account activated successfully (idempotent)"},
        400: {
            "description": "Invalid or expired activation code",
            "content": {"application/json": {"example": {"detail": "Activation code has expired"}}},
        },
        401: {
            "description": "Invalid API credentials",
            "content": {"application/json": {"example": {"detail": "Invalid API credentials"}}},
        },
        404: {
            "description": "Account or activation code not found",
            "content": {"application/json": {"example": {"detail": "Account not found"}}},
        },
        422: {
            "description": "Invalid account ID format or code format",
            "content": {
                "application/json": {"example": {"detail": "Invalid UUID format: not-a-uuid"}}
            },
        },
    },
)
def activate_account(
    account_id: str,
    request: ActivateAccountRequest,
    credentials: HTTPBasicCredentials = Depends(security),
    handler: ActivateAccountHandler = Injected(ActivateAccountHandler),
) -> None:
    """
    Activate an account using the email verification code.

    Requires Basic Auth credentials to prevent unauthorized activation attempts.
    The activation code expires after 60 seconds from account creation.

    Returns: HTTP 200 OK (no response body)

    Security:
    - Basic Auth required (configured via API_USERNAME/API_PASSWORD env vars)
    - Default credentials: username="api", password="secret"
    - Constant-time credential comparison prevents timing attacks

    Business Rules:
    - Account must exist (404 if not found)
    - Activation code must exist and not be expired (60 seconds)
    - Code value must match the generated code
    - Operation is idempotent (activating already-active account succeeds)

    Example:
        curl -X POST "http://localhost:8000/accounts/{uuid}/activate" \\
             -u api:secret \\
             -H "Content-Type: application/json" \\
             -d '{"code": "1234"}'
    """
    if not validate_api_credentials(credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API credentials",
            headers={"WWW-Authenticate": "Basic"},
        )

    try:
        account_id_vo = AccountId.from_string(account_id)
        code_vo = ActivationCode(request.code)

        command = ActivateAccountCommand(account_id=account_id_vo, code=code_vo)

        handler.handle(command)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        ) from e

    except (AccountNotFoundError, ActivationCodeNotFoundError) as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e

    except (ActivationCodeExpiredError, InvalidActivationCodeError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
