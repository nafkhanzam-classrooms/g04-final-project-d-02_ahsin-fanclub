"""
Event Dispatcher — Publish/Subscribe system for network and game events.

Scenes subscribe to event types they care about.  The networking layer
dispatches events when messages arrive from the server.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable

# Type alias for event handler callbacks
EventHandler = Callable[[dict[str, Any]], None]


class EventDispatcher:
    """
    A simple pub/sub event bus.

    Usage:
        dispatcher = EventDispatcher()

        # Subscribe
        dispatcher.subscribe("snapshot", my_handler)

        # Dispatch
        dispatcher.dispatch("snapshot", {"tick": 1024, ...})

        # Unsubscribe
        dispatcher.unsubscribe("snapshot", my_handler)
    """

    def __init__(self) -> None:
        self._listeners: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Register a handler for the given event type."""
        if handler not in self._listeners[event_type]:
            self._listeners[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        try:
            self._listeners[event_type].remove(handler)
        except ValueError:
            pass  # Handler was not registered — silently ignore

    def dispatch(self, event_type: str, data: dict[str, Any] | None = None) -> None:
        """Invoke all handlers registered for *event_type* with *data*."""
        if data is None:
            data = {}
        for handler in self._listeners.get(event_type, []):
            handler(data)

    def clear(self) -> None:
        """Remove all registered handlers."""
        self._listeners.clear()
