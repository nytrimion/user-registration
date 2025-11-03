"""
Application layer for the Account bounded context.

This layer contains use cases (application services) that orchestrate domain
logic to fulfill business workflows. The application layer sits between the
domain layer (business logic) and infrastructure layer (technical details).

Structure:
    - commands/: CQRS command handlers (write operations)
    - queries/: CQRS query handlers (read operations)
    - events/: Domain event handlers (asynchronous reactions)
    - contracts/: Interface contracts for external services

Principles:
    - Orchestrates domain entities and value objects
    - Manages transactions and persistence (via repositories)
    - Remains framework-agnostic (no FastAPI, Flask, etc.)
    - Depends on domain abstractions (repository interfaces)
    - Uses dependency injection for all external dependencies
"""
