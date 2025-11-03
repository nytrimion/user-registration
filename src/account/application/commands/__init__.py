"""
CQRS Command handlers for the Account bounded context.

This module contains command handlers that execute write operations
(create, update, delete) on the Account aggregate.

Commands follow the CQRS (Command Query Responsibility Segregation) pattern:
- Commands represent user intentions (RegisterAccount, ActivateAccount)
- Handlers execute the business logic to fulfill the command
- Commands are immutable (frozen dataclasses)
- Handlers are injected with dependencies via @inject decorator

Pragmatic CQRS Structure:
    For projects with < 10 use cases, we merge Command + Handler in the
    same file to reduce boilerplate while maintaining clear separation
    of concerns.

    Example: register_account.py contains:
        - RegisterAccountCommand (immutable DTO)
        - RegisterAccountHandler (business orchestration)

    This keeps related code together while preserving testability and
    framework independence.
"""
