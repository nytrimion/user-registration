"""
Integration tests for POST /accounts endpoint.

These tests validate the complete HTTP → Application → Domain → Infrastructure
flow for account creation. They use a real PostgreSQL database and FastAPI
TestClient.

Test Strategy:
    - Real database (Docker PostgreSQL service)
    - Real FastAPI app with DI configured
    - Test HTTP request/response (status codes, headers, validation)
    - Test business rules (email uniqueness, password validation)
    - Test error handling (409, 400 responses)

Fixtures:
    - client: FastAPI TestClient with full app (from conftest.py)
    - Unique emails per test to avoid conflicts
"""

import time

from fastapi.testclient import TestClient

ENDPOINT_URL = "/accounts"


def test_create_account_returns_201_for_valid_request(client: TestClient) -> None:
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
    response = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response.status_code == 201
    assert response.text == ""


def test_create_account_with_duplicate_email_returns_409(client: TestClient) -> None:
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
    response1 = client.post(ENDPOINT_URL, json=payload)
    assert response1.status_code == 201

    # Act: Second request with same email fails
    response2 = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response2.status_code == 409
    assert "detail" in response2.json()
    assert "already registered" in response2.json()["detail"].lower()


def test_create_account_with_invalid_email_returns_422(client: TestClient) -> None:
    """
    POST /accounts with invalid email format should return HTTP 400 Bad Request.

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
    response = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_account_with_short_password_returns_422(client: TestClient) -> None:
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
    response = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_account_trims_whitespace_from_email(client: TestClient) -> None:
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
    response = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response.status_code == 201

    # Verify email was trimmed by attempting duplicate registration
    payload_duplicate = {
        "email": unique_email,
        "password": "SecurePass123!",
    }
    response_duplicate = client.post(ENDPOINT_URL, json=payload_duplicate)
    assert response_duplicate.status_code == 409


def test_create_account_normalizes_email_to_lowercase(client: TestClient) -> None:
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
    response1 = client.post(ENDPOINT_URL, json=payload_uppercase)
    assert response1.status_code == 201

    # Act: Attempt duplicate with lowercase
    email_lowercase = email_uppercase.lower()
    payload_lowercase = {
        "email": email_lowercase,
        "password": "SecurePass123!",
    }
    response2 = client.post(ENDPOINT_URL, json=payload_lowercase)

    # Assert
    assert response2.status_code == 409


def test_create_account_with_missing_email_returns_422(client: TestClient) -> None:
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
    response = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()


def test_create_account_with_missing_password_returns_422(client: TestClient) -> None:
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
    response = client.post(ENDPOINT_URL, json=payload)

    # Assert
    assert response.status_code == 422
    assert "detail" in response.json()
