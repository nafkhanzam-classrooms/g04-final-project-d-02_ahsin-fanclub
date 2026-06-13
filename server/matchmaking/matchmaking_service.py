"""
Matchmaking Service — Orchestrates the matchmaking pipeline.

Combines the QueueManager and RoomAllocator to automatically create
rooms when enough players are waiting.  Broadcasts queue status updates
and triggers room creation.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Coroutine

from server.matchmaking.queue_manager import QueueManager
from server.matchmaking.room_allocator import RoomAllocator
from server.rooms.player_session import PlayerSession, PlayerState
from server.rooms.room import Room
from server.rooms.room_manager import RoomManager
from server.shared.schemas import QueueStatusPayload

logger = logging.getLogger(__name__)

SendCallback = Callable[[int, dict[str, Any]], Coroutine[Any, Any, None]]


class MatchmakingService:
    """
    Manages the matchmaking queue and automatic room creation.

    Usage::

        service = MatchmakingService(room_manager, sessions, send_cb)
        await service.add_player(player_id)
        await service.remove_player(player_id)
    """

    def __init__(
        self,
        room_manager: RoomManager,
        sessions: dict[int, PlayerSession],
        send_callback: SendCallback,
    ) -> None:
        self._queue: QueueManager = QueueManager()
        self._allocator: RoomAllocator = RoomAllocator()
        self._room_manager: RoomManager = room_manager
        self._sessions: dict[int, PlayerSession] = sessions
        self._send_callback: SendCallback = send_callback

    @property
    def queue_size(self) -> int:
        """Number of players currently in the queue."""
        return self._queue.size

    async def add_player(self, player_id: int) -> None:
        """
        Add a player to the matchmaking queue.

        If enough players are queued, a room is automatically created
        and a countdown is started.
        """
        session = self._sessions.get(player_id)
        if session is None:
            return

        if not self._queue.enqueue(player_id):
            # Already in queue
            return

        session.state = PlayerState.IN_QUEUE
        logger.info("Player %d added to matchmaking queue", player_id)

        # Notify all queued players about the new queue size
        await self._broadcast_queue_status()

        # Check if we can create a room
        await self._try_create_room()

    async def remove_player(self, player_id: int) -> None:
        """Remove a player from the matchmaking queue."""
        if self._queue.remove(player_id):
            session = self._sessions.get(player_id)
            if session and session.state == PlayerState.IN_QUEUE:
                session.state = PlayerState.CONNECTED
            logger.info("Player %d removed from matchmaking queue", player_id)
            await self._broadcast_queue_status()

    async def _try_create_room(self) -> None:
        """Create a room if enough players are waiting."""
        while self._allocator.should_create_room(self._queue.size):
            room_size = self._allocator.get_room_size(self._queue.size)
            player_ids = self._queue.dequeue(room_size)

            if len(player_ids) < 2:
                # Not enough players after dequeue (e.g., disconnected)
                # Re-queue them
                for pid in player_ids:
                    self._queue.enqueue(pid)
                break

            # Update player sessions
            for pid in player_ids:
                session = self._sessions.get(pid)
                if session:
                    session.state = PlayerState.IN_ROOM

            # Create the room
            room = self._room_manager.create_room(player_ids, self._sessions)

            # Start the countdown in a background task
            asyncio.create_task(room.start_countdown())

            logger.info(
                "Created room %s with %d players: %s",
                room.room_id,
                len(player_ids),
                player_ids,
            )

        # Notify remaining queued players
        await self._broadcast_queue_status()

    async def _broadcast_queue_status(self) -> None:
        """Send queue status to all queued players."""
        status = QueueStatusPayload(
            players_waiting=self._queue.size,
        ).to_dict()

        # We need to iterate the internal queue set for current members
        for pid in list(self._sessions.keys()):
            session = self._sessions.get(pid)
            if session and session.state == PlayerState.IN_QUEUE:
                await self._send_callback(pid, status)
