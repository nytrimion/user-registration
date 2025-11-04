"""
Integration tests for /accounts router.

These tests validate the complete HTTP → Application → Domain → Infrastructure
flow for account creation and activation. They use a real PostgreSQL database
and FastAPI TestClient.

Test Strategy:
    - Real database (Docker PostgreSQL service)
    - Real FastAPI app with DI configured
    - Test HTTP request/response (status codes, headers, validation)
    - Test business rules (email uniqueness, password validation, activation)
    - Test error handling (200, 400, 401, 404, 409, 422 responses)

Fixtures:
    - client: FastAPI TestClient with full app (from conftest.py)
    - account_repository: AccountRepository for querying created accounts
    - account_activation_repository: AccountActivationRepository for retrieving codes
    - Unique emails per test to avoid conflicts
"""

import time

from fastapi.testclient import TestClient

from src.account.domain.repositories.account_activation_repository import (
    AccountActivationRepository,
)
from src.account.domain.repositories.account_repository import AccountRepository
from src.account.domain.value_objects.email import Email

# ─────────────────────────────────────────────────
# URL Helper Functions
# ─────────────────────────────────────────────────


def create_account_url() -> str:
    """Return URL for account creation endpoint."""
    return "/accounts"


def activate_account_url(account_id: str) -> str:
    """Return URL for account activation endpoint."""
    return f"/accounts/{account_id}/activate"


# ─────────────────────────────────────────────────
# POST /accounts - Create Account Endpoint
# ─────────────────────────────────────────────────


class TestCreateAccountEndpoint:
    """Integration tests for POST /accounts (account creation)."""

    def test_returns_201_for_valid_request(self, client: TestClient) -> None:
        """
        POST /accounts with valid payload should return HTTP 201 Created.

        Validates:
            - Valid email and password accepted
            - Response status 201
            - No response body (as per design)
        """
        # Arrange
        unique_email = f"user-{int(time.time() * 1000)}@example.com"
        payload = {
            "email": unique_email,
            "password": "SecurePass123!",
        }

        # Act
        response = client.post(create_account_url(), json=payload)

        # Assert
        assert response.status_code == 201
        assert response.text == ""

    def test_with_duplicate_email_returns_409(self, client: TestClient) -> None:
        """
        POST /accounts with duplicate email should return HTTP 409 Conflict.

        Validates:
            - Email uniqueness business rule enforced
            - Second request with same email rejected
            - Error message indicates duplicate email
        """
        # Arrange
        unique_email = f"duplicate-{int(time.time() * 1000)}@example.com"
        payload = {
            "email": unique_email,
            "password": "SecurePass123!",
        }

        # Act: First request succeeds
        response1 = client.post(create_account_url(), json=payload)
        assert response1.status_code == 201

        # Act: Second request with same email fails
        response2 = client.post(create_account_url(), json=payload)

        # Assert
        assert response2.status_code == 409
        assert "detail" in response2.json()
        assert "already registered" in response2.json()["detail"].lower()

    def test_with_invalid_email_returns_422(self, client: TestClient) -> None:
        """
        POST /accounts with invalid email format should return HTTP 422.

        Validates:
            - Pydantic EmailStr validation works
            - Invalid email format rejected at HTTP layer
            - Error details provided
        """
        # Arrange
        payload = {
            "email": "not-an-email",
            "password": "SecurePass123!",
        }

        # Act
        response = client.post(create_account_url(), json=payload)

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_with_short_password_returns_422(self, client: TestClient) -> None:
        """
        POST /accounts with password < 8 chars should return HTTP 422.

        Validates:
            - Pydantic Field(min_length=8) validation works
            - Password length constraint enforced at HTTP layer
        """
        # Arrange
        unique_email = f"user-{int(time.time() * 1000)}@example.com"
        payload = {
            "email": unique_email,
            "password": "short",
        }

        # Act
        response = client.post(create_account_url(), json=payload)

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_trims_whitespace_from_email(self, client: TestClient) -> None:
        """
        POST /accounts should trim whitespace from email (Pydantic ConfigDict).

        Validates:
            - str_strip_whitespace=True configuration works
            - Email with surrounding spaces normalized
        """
        # Arrange
        unique_email = f"user-{int(time.time() * 1000)}@example.com"
        payload = {
            "email": f"  {unique_email}  ",
            "password": "SecurePass123!",
        }

        # Act
        response = client.post(create_account_url(), json=payload)

        # Assert
        assert response.status_code == 201

        # Verify email was trimmed by attempting duplicate registration
        payload_duplicate = {
            "email": unique_email,
            "password": "SecurePass123!",
        }
        response_duplicate = client.post(create_account_url(), json=payload_duplicate)
        assert response_duplicate.status_code == 409

    def test_normalizes_email_to_lowercase(self, client: TestClient) -> None:
        """
        POST /accounts should normalize email to lowercase (Email VO).

        Validates:
            - Email VO normalization works through HTTP layer
            - Uppercase email converted to lowercase
            - Case-insensitive duplicate detection
        """
        # Arrange
        timestamp = int(time.time() * 1000)
        email_uppercase = f"USER-{timestamp}@EXAMPLE.COM"
        payload_uppercase = {
            "email": email_uppercase,
            "password": "SecurePass123!",
        }

        # Act: Create with uppercase email
        response1 = client.post(create_account_url(), json=payload_uppercase)
        assert response1.status_code == 201

        # Act: Attempt duplicate with lowercase
        email_lowercase = email_uppercase.lower()
        payload_lowercase = {
            "email": email_lowercase,
            "password": "SecurePass123!",
        }
        response2 = client.post(create_account_url(), json=payload_lowercase)

        # Assert
        assert response2.status_code == 409

    def test_with_missing_email_returns_422(self, client: TestClient) -> None:
        """
        POST /accounts with missing email field should return HTTP 422.

        Validates:
            - Required field validation works
            - Pydantic validation error for missing field
        """
        # Arrange
        payload = {
            "password": "SecurePass123!",
            # email missing
        }

        # Act
        response = client.post(create_account_url(), json=payload)

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_with_missing_password_returns_422(self, client: TestClient) -> None:
        """
        POST /accounts with missing password field should return HTTP 422.

        Validates:
            - Required field validation works
            - Pydantic validation error for missing field
        """
        # Arrange
        unique_email = f"user-{int(time.time() * 1000)}@example.com"
        payload = {
            "email": unique_email,
            # password missing
        }

        # Act
        response = client.post(create_account_url(), json=payload)

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()


# ─────────────────────────────────────────────────
# POST /accounts/{id}/activate - Activate Account Endpoint
# ─────────────────────────────────────────────────


class TestActivateAccountEndpoint:
    """Integration tests for POST /accounts/{id}/activate (account activation)."""

    def test_returns_200_for_valid_activation(
        self,
        client: TestClient,
        account_repository: AccountRepository,
        account_activation_repository: AccountActivationRepository,
    ) -> None:
        """
        POST /accounts/{id}/activate with valid code and auth should return HTTP 200.

        Validates:
            - Account activated successfully
            - Valid Basic Auth credentials accepted
            - Valid activation code accepted
            - Response status 200
            - No response body
        """
        # Arrange: Create account
        unique_email = f"activate-{int(time.time() * 1000)}@example.com"
        create_payload = {"email": unique_email, "password": "SecurePass123!"}
        create_response = client.post(create_account_url(), json=create_payload)
        assert create_response.status_code == 201

        # Arrange: Get account_id and activation_code from database
        account = account_repository.find_by_email(Email(unique_email))
        assert account is not None, "Account should exist after creation"

        activation = account_activation_repository.find_by_account_id(account.id)
        assert activation is not None, "Activation code should exist after creation"

        # Act
        url = activate_account_url(str(account.id.value))
        response = client.post(
            url,
            json={"code": activation.code.code},
            auth=("api", "secret"),  # Basic Auth credentials
        )

        # Assert
        assert response.status_code == 200
        assert response.text == ""

    def test_returns_200_when_account_already_activated(
        self,
        client: TestClient,
        account_repository: AccountRepository,
        account_activation_repository: AccountActivationRepository,
    ) -> None:
        """
        POST /accounts/{id}/activate on already-active account should return HTTP 200.

        Validates:
            - Idempotent operation (no error on repeated activation)
            - Second activation succeeds with 200
        """
        # Arrange: Create and activate account
        unique_email = f"idempotent-{int(time.time() * 1000)}@example.com"
        create_payload = {"email": unique_email, "password": "SecurePass123!"}
        create_response = client.post(create_account_url(), json=create_payload)
        assert create_response.status_code == 201

        # Arrange: Get account_id and activation_code
        account = account_repository.find_by_email(Email(unique_email))
        assert account is not None

        activation = account_activation_repository.find_by_account_id(account.id)
        assert activation is not None

        # Act: First activation
        url = activate_account_url(str(account.id.value))
        response1 = client.post(url, json={"code": activation.code.code}, auth=("api", "secret"))
        assert response1.status_code == 200

        # Act: Second activation (idempotent)
        response2 = client.post(url, json={"code": activation.code.code}, auth=("api", "secret"))

        # Assert
        assert response2.status_code == 200

    def test_returns_401_for_invalid_basic_auth_credentials(self, client: TestClient) -> None:
        """
        POST /accounts/{id}/activate with invalid Basic Auth should return HTTP 401.

        Validates:
            - Invalid username/password rejected
            - WWW-Authenticate header present
            - Error message indicates invalid credentials
        """
        # Arrange
        account_id = "019..."  # Any UUID (validation happens before account lookup)
        url = activate_account_url(account_id)

        # Act: Invalid credentials
        response = client.post(url, json={"code": "1234"}, auth=("wrong", "credentials"))

        # Assert
        assert response.status_code == 401
        assert "detail" in response.json()
        assert "www-authenticate" in response.headers
        assert response.headers["www-authenticate"] == "Basic"

    def test_returns_401_for_missing_basic_auth_header(self, client: TestClient) -> None:
        """
        POST /accounts/{id}/activate without Authorization header should return HTTP 401.

        Validates:
            - Missing Basic Auth rejected
            - WWW-Authenticate header triggers browser prompt
        """
        # Arrange
        account_id = "019..."
        url = activate_account_url(account_id)

        # Act: No auth parameter
        response = client.post(url, json={"code": "1234"})

        # Assert
        assert response.status_code == 401
        assert "www-authenticate" in response.headers

    def test_returns_422_for_invalid_uuid_format(self, client: TestClient) -> None:
        """
        POST /accounts/{id}/activate with invalid UUID should return HTTP 422.

        Validates:
            - AccountId.from_string() ValueError mapped to 422
            - Invalid UUID format rejected before domain logic
        """
        # Arrange: Invalid UUID format
        url = activate_account_url("not-a-uuid")

        # Act
        response = client.post(url, json={"code": "1234"}, auth=("api", "secret"))

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()

    def test_returns_422_for_invalid_code_format(self, client: TestClient) -> None:
        r"""
        POST /accounts/{id}/activate with non-numeric code should return HTTP 422.

        Validates:
            - Pydantic Field(pattern=r"^\d{4}$") validation
            - Non-numeric code rejected before domain logic
        """
        # Arrange
        from src.account.domain.value_objects.account_id import AccountId

        account_id = str(AccountId.generate().value)
        url = activate_account_url(account_id)

        # Act: Non-numeric code
        response = client.post(url, json={"code": "abcd"}, auth=("api", "secret"))

        # Assert
        assert response.status_code == 422
        assert "detail" in response.json()
