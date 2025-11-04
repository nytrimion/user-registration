"""
Event dispatcher interface.

Defines the contract for event dispatching across the application.
Infrastructure layer provides concrete implementations (synchronous, async, etc.).
"""

from abc import ABC, abstractmethod


class EventDispatcher(ABC):
    """
    Abstract interface for event dispatching.

    This interface defines the contract for dispatching domain events to
    registered handlers. Concrete implementations can be synchronous,
    asynchronous, or use message queues.

    Design Principles:
        - Framework-agnostic (no FastAPI, no HTTP dependencies)
        - Interface in domain layer, implementations in infrastructure
        - Supports polymorphism (swap implementations without changing domain)

    Implementations:
        - InMemoryEventDispatcher: Synchronous, in-process (MVP)
        - AsyncEventDispatcher: Thread-based, asynchronous (future)
        - CeleryEventDispatcher: Distributed, Redis-backed (production)

    Example:
        # Register event handler
        dispatcher.register(AccountCreated, AccountCreatedHandler)

        # Dispatch event (implementation-specific behavior)
        dispatcher.dispatch(AccountCreated(account.id, account.email, ...))
    """

    @abstractmethod
    def register(self, event_type: type, handler_type: type) -> None:
        """
        Register event handler for given event type.

        Args:
            event_type: Domain event class (e.g., AccountCreated)
            handler_type: Handler class (e.g., AccountCreatedHandler)

        Notes:
            - Handlers are resolved via dependency injection (injector)
            - Multiple handlers per event not supported in MVP (YAGNI)
            - Handler must have handle(event) method
        """
        pass

    @abstractmethod
    def dispatch(self, event: object) -> None:
        """
        Dispatch event to registered handler.

        Behavior depends on implementation:
        - Synchronous: Executes handler immediately, blocks caller
        - Asynchronous: Queues event, returns immediately

        Args:
            event: Domain event instance

        Notes:
            - No return value (fire-and-forget pattern)
            - Errors handled by implementation (log, retry, dead-letter queue)
            - If no handler registered, silently ignores (idempotent)
        """
        pass
