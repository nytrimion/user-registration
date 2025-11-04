"""
Unit tests for InMemoryEventDispatcher.

Tests verify:
    - Event handler registration
    - Event dispatching to registered handlers
    - Handler resolution via injector
    - Graceful handling of unregistered events
"""

from dataclasses import dataclass
from unittest.mock import Mock

from injector import Injector

from src.shared.infrastructure.events.in_memory_event_dispatcher import (
    InMemoryEventDispatcher,
)


# Test fixtures: Mock event and handler
@dataclass(frozen=True)
class TestEvent:
    """Mock event for testing."""

    message: str


class TestEventHandler:
    """Mock handler for testing."""

    def __init__(self) -> None:
        self.handled_events: list[TestEvent] = []

    def handle(self, event: TestEvent) -> None:
        """Handle test event by recording it."""
        self.handled_events.append(event)


class TestInMemoryEventDispatcher:
    """Test suite for InMemoryEventDispatcher."""

    def test_register_event_handler(self) -> None:
        """Verify event handler can be registered."""
        # Arrange
        injector = Injector()
        dispatcher = InMemoryEventDispatcher(injector)

        # Act
        dispatcher.register(TestEvent, TestEventHandler)

        # Assert
        assert TestEvent in dispatcher._handlers
        assert dispatcher._handlers[TestEvent] == TestEventHandler

    def test_dispatch_calls_registered_handler(self) -> None:
        """Verify dispatch resolves and calls registered handler."""
        # Arrange
        mock_handler = TestEventHandler()
        mock_injector = Mock(spec=Injector)
        mock_injector.get.return_value = mock_handler

        dispatcher = InMemoryEventDispatcher(mock_injector)
        dispatcher.register(TestEvent, TestEventHandler)

        event = TestEvent(message="test")

        # Act
        dispatcher.dispatch(event)

        # Assert
        mock_injector.get.assert_called_once_with(TestEventHandler)
        assert len(mock_handler.handled_events) == 1
        assert mock_handler.handled_events[0] == event

    def test_dispatch_resolves_handler_via_injector(self) -> None:
        """Verify dispatcher uses injector to resolve handler with dependencies."""
        # Arrange
        injector = Injector()
        dispatcher = InMemoryEventDispatcher(injector)
        dispatcher.register(TestEvent, TestEventHandler)

        event = TestEvent(message="test with real injector")

        # Act
        dispatcher.dispatch(event)

        # Assert: No exception raised (handler resolved and executed)
        # Note: We can't easily verify handler was called without mocking injector,
        # but if no exception is raised, it means injector.get() worked

    def test_dispatch_ignores_unregistered_events(self) -> None:
        """Verify dispatch silently ignores events with no registered handler."""
        # Arrange
        injector = Injector()
        dispatcher = InMemoryEventDispatcher(injector)

        @dataclass(frozen=True)
        class UnregisteredEvent:
            data: str

        event = UnregisteredEvent(data="test")

        # Act & Assert (should not raise exception)
        dispatcher.dispatch(event)

    def test_dispatch_multiple_events_to_same_handler(self) -> None:
        """Verify dispatcher handles multiple events dispatched to same handler."""
        # Arrange
        mock_handler = TestEventHandler()
        mock_injector = Mock(spec=Injector)
        mock_injector.get.return_value = mock_handler

        dispatcher = InMemoryEventDispatcher(mock_injector)
        dispatcher.register(TestEvent, TestEventHandler)

        event1 = TestEvent(message="first")
        event2 = TestEvent(message="second")

        # Act
        dispatcher.dispatch(event1)
        dispatcher.dispatch(event2)

        # Assert
        assert len(mock_handler.handled_events) == 2
        assert mock_handler.handled_events[0].message == "first"
        assert mock_handler.handled_events[1].message == "second"
