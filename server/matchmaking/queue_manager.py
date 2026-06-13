"""
Queue Manager — FIFO matchmaking queue.

Players are added and removed from the queue.  The MatchmakingService
polls this queue to form matches.
"""

from __future__ import annotations

import logging
from collections import deque

logger = logging.getLogger(__name__)


class QueueManager:
    """
    Simple FIFO queue for players waiting for a match.

    Thread-safety is not required — runs on a single asyncio loop.
    """

    def __init__(self) -> None:
        self._queue: deque[int] = deque()
        self._in_queue: set[int] = set()  # O(1) membership check

    def enqueue(self, player_id: int) -> bool:
        """
        Add a player to the queue.

        Returns True if the player was added, False if already queued.
        """
        if player_id in self._in_queue:
            return False
        self._queue.append(player_id)
        self._in_queue.add(player_id)
        logger.info("Player %d joined queue (size: %d)", player_id, self.size)
        return True

    def dequeue(self, count: int) -> list[int]:
        """
        Remove and return up to *count* players from the front of the queue.
        """
        result: list[int] = []
        while self._queue and len(result) < count:
            pid = self._queue.popleft()
            if pid in self._in_queue:
                self._in_queue.discard(pid)
                result.append(pid)
        return result

    def remove(self, player_id: int) -> bool:
        """
        Remove a specific player from the queue.

        Returns True if the player was in the queue.
        """
        if player_id not in self._in_queue:
            return False
        self._in_queue.discard(player_id)
        # Lazy removal — the deque still has the player, but they're
        # no longer in _in_queue so dequeue() will skip them.
        logger.info("Player %d left queue (size: %d)", player_id, self.size)
        return True

    @property
    def size(self) -> int:
        """Number of players currently in the queue."""
        return len(self._in_queue)

    def contains(self, player_id: int) -> bool:
        """Check if a player is in the queue."""
        return player_id in self._in_queue

    def peek(self, count: int) -> list[int]:
        """Peek at the first *count* players without removing them."""
        result: list[int] = []
        for pid in self._queue:
            if pid in self._in_queue:
                result.append(pid)
                if len(result) >= count:
                    break
        return result

    def clear(self) -> None:
        """Clear the queue."""
        self._queue.clear()
        self._in_queue.clear()
