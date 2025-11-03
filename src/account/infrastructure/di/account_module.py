"""
Dependency injection module for account bounded context.

This module configures the injector Module for account-specific bindings
(repositories, handlers, services). It provides singleton instances for
resources within the account bounded context.

Design Decisions:
    - Singleton scope: Repository shared across all requests
    - Provider pattern: @provider methods for initialization
    - Bounded context isolation: Account module independent of other BCs
    - Interface binding: Domain interface → Infrastructure implementation

Architecture:
    - AccountModule: Binds account-specific dependencies
    - InfrastructureModule: Shared resources (database pool)
    - Composition: Injector([InfrastructureModule(), AccountModule()])

Usage Example:
    ```python
    # In main.py (application startup)
    from injector import Injector
    from fastapi_injector import attach_injector

    from src.shared.infrastructure.di.container import InfrastructureModule
    from src.account.infrastructure.di.account_module import AccountModule

    injector = Injector([
        InfrastructureModule(),  # Shared resources (database)
        AccountModule(),          # Account bounded context
    ])

    app = FastAPI()
    attach_injector(app, injector)
    ```
"""

from injector import Module, provider, singleton

from src.account.domain.repositories.account_repository import AccountRepository
from src.account.infrastructure.persistence.postgres_account_repository import (
    PostgresAccountRepository,
)


class AccountModule(Module):
    """
    Dependency injection module for account bounded context.

    Configures bindings for account-specific dependencies (repositories,
    use case handlers, domain services). This module is loaded at application
    startup and provides singleton instances for account resources.

    Bindings:
        - AccountRepository → PostgresAccountRepository (singleton)

    Singleton Justification:
        - Repository is stateless (no mutable state)
        - Connection pool managed by DatabaseConnectionFactory (injected)
        - Thread-safe for concurrent requests
        - Single instance reduces memory overhead

    Future Bindings:
        - RegisterAccountHandler (application layer)
        - ActivateAccountHandler (application layer)
        - AccountCreatedEventHandler (event handler)

    Testing:
        - Unit tests: Provide mock/fake implementations
        - Integration tests: Use same AccountModule with real PostgreSQL
    """

    @singleton
    @provider
    def provide_account_repository(
        self, repository: PostgresAccountRepository
    ) -> AccountRepository:
        """
        Provide singleton AccountRepository for dependency injection.

        Binds the domain interface (AccountRepository) to the infrastructure
        implementation (PostgresAccountRepository). This preserves Clean
        Architecture by keeping the domain layer independent of infrastructure.

        Args:
            repository: PostgresAccountRepository instance (auto-injected)
                Injector automatically resolves PostgresAccountRepository
                by injecting DatabaseConnectionFactory into its constructor

        Returns:
            AccountRepository: Singleton instance of PostgresAccountRepository

        Lifecycle:
            - Created: Application startup (first injection request)
            - Reused: All subsequent injections get same instance
            - Destroyed: Application shutdown

        Dependency Chain:
            AccountRepository
            └─> PostgresAccountRepository(@inject)
                └─> DatabaseConnectionFactory (from InfrastructureModule)

        Example:
            ```python
            # In application handler
            @inject
            def __init__(self, repository: AccountRepository):
                self._repository = repository  # Gets PostgresAccountRepository
            ```
        """
        return repository
