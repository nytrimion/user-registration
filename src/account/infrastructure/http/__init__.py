"""
HTTP infrastructure for account bounded context.

This package contains HTTP controllers and DTOs for account-related endpoints.
Controllers handle request/response mapping and delegate business logic to
application layer handlers.

Architecture:
    - Controllers: FastAPI routers with dependency injection
    - DTOs: Pydantic models for request/response validation
    - Error handlers: HTTP exception mapping from domain exceptions
"""
