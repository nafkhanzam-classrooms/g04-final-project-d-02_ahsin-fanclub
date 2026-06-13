"""
Event Bus — Asynchronous publish / subscribe for internal server events.

Components subscribe to event *types* and receive them asynchronously
when another component publishes.  This decouples networking, matchmaking,
and room management cleanly.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any, Callable, Coroutine

logger = logging.getLogger(__name__)

# Type alias for async event handlers
EventHandler = Callable[[Any], Coroutine[Any, Any, None]]


class EventBus:
    """
    Async pub/sub event bus.

    Usage::

        bus = EventBus()

        async def on_player_joined(event: PlayerJoinedQueue):
            print(event.player_id)

        bus.subscribe(PlayerJoinedQueue, on_player_joined)
        await bus.publish(PlayerJoinedQueue(player_id=1))
    """

    def __init__(self) -> None:
        self._handlers: dict[type, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type, handler: EventHandler) -> None:
        """Register an async handler for *event_type*."""
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: type, handler: EventHandler) -> None:
        """Remove a previously registered handler."""
        try:
            self._handlers[event_type].remove(handler)
        except ValueError:
            pass

    async def publish(self, event: Any) -> None:
        """
        Invoke all handlers registered for the event's type.

        Handlers run concurrently via ``asyncio.gather`` so one slow
        handler doesn't block others.
        """
        event_type = type(event)
        handlers = self._handlers.get(event_type, [])
        if not handlers:
            return

        tasks = [h(event) for h in handlers]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.exception(
                    "Event handler %s raised an exception for %s: %s",
                    handlers[i].__name__,
                    event_type.__name__,
                    result,
                )

    def clear(self) -> None:
        """Remove all handlers."""
        self._handlers.clear()
