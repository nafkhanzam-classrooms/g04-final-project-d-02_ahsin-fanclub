"""
Message Router — Dispatches decoded client messages to the appropriate handler.

Validates incoming packets, enforces rate limiting, and routes each
message type to its registered handler coroutine.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Coroutine

from server.networking.protocol import VALID_CLIENT_TYPES
from server.networking.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

# Type alias for message handler coroutines
MessageHandler = Callable[[int, dict[str, Any]], Coroutine[Any, Any, None]]


class MessageRouter:
    """
    Routes validated client messages to registered handler coroutines.

    Usage::

        router = MessageRouter(rate_limiter)
        router.register("join_queue", handle_join_queue)
        router.register("input", handle_input)

        # Called from the WebSocket receive loop:
        await router.route(player_id, decoded_message)
    """

    def __init__(self, rate_limiter: RateLimiter) -> None:
        self._rate_limiter: RateLimiter = rate_limiter
        self._handlers: dict[str, MessageHandler] = {}

    def register(self, message_type: str, handler: MessageHandler) -> None:
        """Register a handler for a specific message type."""
        self._handlers[message_type] = handler
        logger.debug("Registered handler for '%s'", message_type)

    async def route(self, player_id: int, message: dict[str, Any]) -> None:
        """
        Validate and route a decoded client message.

        Steps:
            1. Validate the message has a ``type`` field.
            2. Check that the type is a known client message type.
            3. Enforce rate limiting.
            4. Dispatch to the registered handler.
        """
        msg_type = message.get("type")

        if not msg_type:
            logger.warning("Player %d: message missing 'type' field", player_id)
            return

        if msg_type not in VALID_CLIENT_TYPES:
            logger.warning(
                "Player %d: unknown message type '%s'", player_id, msg_type
            )
            return

        if not self._rate_limiter.allow(player_id):
            logger.warning("Player %d: rate limited", player_id)
            return

        handler = self._handlers.get(msg_type)
        if handler is None:
            logger.warning(
                "Player %d: no handler for '%s'", player_id, msg_type
            )
            return

        try:
            await handler(player_id, message)
        except Exception:
            logger.exception(
                "Player %d: handler for '%s' raised an exception",
                player_id,
                msg_type,
            )

    def remove_player(self, player_id: int) -> None:
        """Clean up any per-player state (delegates to rate limiter)."""
        self._rate_limiter.remove_player(player_id)
