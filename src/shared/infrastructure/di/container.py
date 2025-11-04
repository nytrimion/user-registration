"""
Dependency injection container for shared infrastructure.

This module configures the injector Module for shared infrastructure bindings
(database, email, external services). It provides singleton instances for
resources that are shared across all bounded contexts.

Design Decisions:
    - Singleton scope: Shared resources initialized once (connection pool)
    - Provider pattern: @provider methods for complex initialization logic
    - Module separation: Shared infrastructure isolated from bounded contexts
    - Testability: Can be replaced with TestModule for integration tests

Architecture:
    - InfrastructureModule: Binds shared infrastructure (database, email, etc.)
    - Bounded Context Modules: Each BC defines its own module (AccountModule, etc.)
    - Composition: Injector([InfrastructureModule(), AccountModule(), ...])

Usage Example:
    ```python
    # In main.py (application startup)
    from injector import Injector
    from fastapi_injector import attach_injector

    from src.shared.infrastructure.di.container import InfrastructureModule
    from src.account.infrastructure.di.account_module import AccountModule

    injector = Injector([
        InfrastructureModule(),  # Shared resources
        AccountModule(),          # Account bounded context
    ])

    app = FastAPI()
    attach_injector(app, injector)
    ```
"""

from injector import Binder, Module, provider, singleton

from src.shared.application.services.email_service import EmailService
from src.shared.domain.events.event_dispatcher import EventDispatcher
from src.shared.infrastructure.database.connection import (
    DatabaseConnectionFactory,
    PostgresConnectionFactory,
)
from src.shared.infrastructure.events.in_memory_event_dispatcher import (
    InMemoryEventDispatcher,
)
from src.shared.infrastructure.services.logger_email_service import (
    LoggerEmailService,
)


class InfrastructureModule(Module):
    """
    Dependency injection module for shared infrastructure layer.

    Configures bindings for infrastructure dependencies that are shared across
    all bounded contexts (database connections, email services, logging, etc.).
    This module is loaded at application startup and provides singleton instances
    for shared resources.

    Bindings:
        - DatabaseConnectionFactory → PostgresConnectionFactory (singleton)
        - EventDispatcher → InMemoryEventDispatcher (singleton)
        - EmailService → LoggerEmailService (singleton)

    Singleton Justification:
        - Connection pool: Created once and reused (thread-safe pool)
        - Event dispatcher: Single registry for all event→handler mappings
        - Email service: Stateless, thread-safe, no per-request state
        - Shared resources prevent duplication and ensure consistency

    Future Bindings:
        - EmailService → SMTPEmailService or SendGridEmailService (production)
        - Logger → StructuredLogger

    Testing:
        - Unit tests: Provide mock/fake implementations
        - Integration tests: Use same InfrastructureModule with real DB
    """

    def configure(self, binder: Binder) -> None:
        """
        Configure dependency injection bindings.

        This method is called by the injector at startup to register
        interface→implementation mappings.

        Args:
            binder: Injector binder for dependency registration
        """
        # Event dispatcher (singleton - one registry for entire application)
        binder.bind(
            EventDispatcher,  # type: ignore[type-abstract]
            to=InMemoryEventDispatcher,
            scope=singleton,
        )

        # Email service (singleton - stateless logger implementation)
        binder.bind(
            EmailService,  # type: ignore[type-abstract]
            to=LoggerEmailService,
            scope=singleton,
        )

    @singleton
    @provider
    def provide_database_connection_factory(self) -> DatabaseConnectionFactory:
        """
        Provide singleton DatabaseConnectionFactory for dependency injection.

        Creates a PostgresConnectionFactory with connection pool initialized
        from environment variables. The pool is created once at application
        startup and reused for all database operations across all bounded contexts.

        Returns:
            DatabaseConnectionFactory: Singleton instance of PostgresConnectionFactory

        Lifecycle:
            - Created: Application startup (first injection request)
            - Reused: All subsequent injections get same instance
            - Closed: Application shutdown (via shutdown event)

        Thread Safety:
            - PostgresConnectionFactory uses ThreadedConnectionPool
            - Safe to inject in multiple FastAPI workers
            - Pool handles concurrent connection requests

        Environment Configuration:
            Reads from environment variables (same as docker-compose.yml):
            - DATABASE_HOST (default: postgres)
            - DATABASE_PORT (default: 5432)
            - DATABASE_NAME (default: user_registration)
            - DATABASE_USER (default: postgres)
            - DATABASE_PASSWORD (default: postgres)
        """
        return PostgresConnectionFactory()
