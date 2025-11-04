"""
Synchronous in-memory event dispatcher.

ARCHITECTURE DECISION RECORD (ADR):

Problem:
    Event handlers (e.g., send activation email) should ideally execute
    asynchronously to avoid blocking HTTP responses during I/O operations.

Decision:
    Use EventDispatcher interface with synchronous implementation for MVP.

Rationale:
    - Demonstrates clean architecture (interface vs implementation separation)
    - Faster to implement and test (no threading/queue complexity)
    - Allows focus on core business logic (activation code, email service)
    - Easy to swap later: InMemoryEventDispatcher → AsyncEventDispatcher

Trade-offs:
    - Blocks main thread until event handler completed event processing
    - Acceptable for test technique scope and demonstration purposes
    - Production evolution: replace with async implementation (see below)

Future Evolution Path:
    from queue import Queue
    from threading import Thread

    class AsyncEventDispatcher(EventDispatcher):
        @inject
        def __init__(self, injector: Injector):
            self._injector = injector
            self._handlers: Dict[Type, Type] = {}
            self._queue: Queue[object] = Queue()
            self._worker = Thread(target=self._process_events, daemon=True)
            self._worker.start()

        def dispatch(self, event: object) -> None:
            self._queue.put(event)  # Non-blocking return

        def _process_events(self) -> None:
            while True:
                event = self._queue.get()
                handler_type = self._handlers.get(type(event))
                if handler_type:
                    handler = self._injector.get(handler_type)
                    handler.handle(event)
                self._queue.task_done()
"""

from injector import Injector, inject

from src.shared.domain.events.event_dispatcher import EventDispatcher


class InMemoryEventDispatcher(EventDispatcher):
    """
    Synchronous in-memory event dispatcher.

    Events are dispatched synchronously in the same thread as the caller.
    The caller WAITS for event handler completion before continuing.

    Architecture:
        - Handlers resolved via injector (with all dependencies)
        - Registry pattern: dict[event_type -> handler_type]
        - Framework-agnostic (works in HTTP, CLI, background jobs)

    Example:
        # Registration (in main.py)
        dispatcher.register(AccountCreated, AccountCreatedHandler)

        # Dispatch (in RegisterAccountHandler)
        dispatcher.dispatch(AccountCreated(...))
        # Handler executes synchronously before return

    Notes:
        - Single handler per event type (YAGNI for MVP)
        - Errors propagate to caller (no retry mechanism)
        - Silently ignores events with no registered handler
    """

    @inject
    def __init__(self, injector: Injector):
        """
        Initialize dispatcher with injector.

        Args:
            injector: Injector instance for resolving event handlers
        """
        self._injector = injector
        self._handlers: dict[type, type] = {}

    def register(self, event_type: type, handler_type: type) -> None:
        """
        Register event handler for given event type.

        Args:
            event_type: Domain event class (e.g., AccountCreated)
            handler_type: Handler class (e.g., AccountCreatedHandler)
        """
        self._handlers[event_type] = handler_type

    def dispatch(self, event: object) -> None:
        """
        Dispatch event synchronously (blocking).

        Resolves handler via injector and executes immediately.
        Caller WAITS for handler completion before continuing.

        Args:
            event: Domain event instance

        Behavior:
            - If handler registered: resolve via injector and call handle(event)
            - If no handler: silently ignore (idempotent)
            - If handler raises exception: propagate to caller
        """
        handler_type = self._handlers.get(type(event))
        if handler_type:
            handler: object = self._injector.get(handler_type)
            handler.handle(event)  # type: ignore[attr-defined]
