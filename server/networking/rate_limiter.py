"""
Rate Limiter — Prevents packet spam from individual players.

Uses a sliding-window token-bucket algorithm: each player is allowed
at most ``max_messages`` within a rolling ``window`` of seconds.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field

from server.shared.constants import RATE_LIMIT_MAX_MESSAGES, RATE_LIMIT_WINDOW


@dataclass
class _PlayerBucket:
    """Per-player message timestamps for rate limiting."""
    timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """
    Per-player sliding-window rate limiter.

    Usage::

        limiter = RateLimiter()
        if limiter.allow(player_id):
            process_message()
        else:
            drop_or_warn()
    """

    def __init__(
        self,
        window: float = RATE_LIMIT_WINDOW,
        max_messages: int = RATE_LIMIT_MAX_MESSAGES,
    ) -> None:
        self._window: float = window
        self._max_messages: int = max_messages
        self._buckets: dict[int, _PlayerBucket] = defaultdict(_PlayerBucket)

    def allow(self, player_id: int) -> bool:
        """
        Check if the player is allowed to send a message.

        Returns True if the message is allowed, False if rate-limited.
        """
        now = time.monotonic()
        bucket = self._buckets[player_id]

        cutoff = now - self._window
        bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]

        if len(bucket.timestamps) >= self._max_messages:
            return False

        bucket.timestamps.append(now)
        return True

    def remove_player(self, player_id: int) -> None:
        """Clean up tracking data for a disconnected player."""
        self._buckets.pop(player_id, None)

    def reset(self) -> None:
        """Clear all tracking data."""
        self._buckets.clear()
