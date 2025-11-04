"""
HTTP authentication utilities for FastAPI endpoints.

This module provides reusable authentication functions for securing HTTP endpoints
across all bounded contexts. Implements security best practices for credential
validation.

Design Decisions:
    - Environment-based configuration for flexibility
    - Constant-time comparison to prevent timing attacks
    - Reusable across all routers requiring Basic Auth

Security:
    - Uses secrets.compare_digest() for timing attack prevention
    - Credentials configurable via environment variables
    - No hardcoded secrets in production code

Usage Example:
    ```python
    from fastapi import Depends
    from fastapi.security import HTTPBasic, HTTPBasicCredentials
    from src.shared.infrastructure.http.auth import validate_api_credentials

    security = HTTPBasic()

    @router.post("/protected-endpoint")
    def protected_route(credentials: HTTPBasicCredentials = Depends(security)):
        if not validate_api_credentials(credentials):
            raise HTTPException(401, "Invalid credentials",
                              headers={"WWW-Authenticate": "Basic"})
        # ... endpoint logic
    ```
"""

import os
import secrets

from fastapi.security import HTTPBasicCredentials

# API Basic Auth credentials (configurable via environment)
# Default values: username="api", password="secret"
# Override with API_USERNAME and API_PASSWORD env vars
#
# Example usage for API consumers:
#   curl -X POST "http://localhost:8000/endpoint" -u api:secret
#
# Production deployment:
#   export API_USERNAME="prod_username"
#   export API_PASSWORD="secure_random_password"
API_USERNAME = os.getenv("API_USERNAME", "api")
API_PASSWORD = os.getenv("API_PASSWORD", "secret")


def validate_api_credentials(credentials: HTTPBasicCredentials) -> bool:
    """
    Validate API credentials using constant-time comparison.

    Args:
        credentials: HTTPBasicCredentials from Authorization header

    Returns:
        True if credentials match configured API username/password, False otherwise

    Security:
        Uses secrets.compare_digest() to prevent timing attacks. This ensures
        that comparison takes constant time regardless of where strings differ,
        preventing attackers from guessing credentials character-by-character
        based on response time variations.

        Timing attacks work by measuring response time:
        - String comparison stops at first mismatch (faster for early mismatches)
        - Attacker tries "a", "b", "c"... and measures response time
        - Slower response = correct character (comparison went further)
        - secrets.compare_digest() always takes same time regardless of mismatch

    Example:
        >>> from fastapi.security import HTTPBasicCredentials
        >>> creds = HTTPBasicCredentials(username="api", password="secret")
        >>> validate_api_credentials(creds)
        True
        >>> creds_wrong = HTTPBasicCredentials(username="wrong", password="bad")
        >>> validate_api_credentials(creds_wrong)
        False
    """
    username_bytes = credentials.username.encode("utf8")
    password_bytes = credentials.password.encode("utf8")
    correct_username_bytes = API_USERNAME.encode("utf8")
    correct_password_bytes = API_PASSWORD.encode("utf8")

    username_match = secrets.compare_digest(username_bytes, correct_username_bytes)
    password_match = secrets.compare_digest(password_bytes, correct_password_bytes)

    return username_match and password_match
