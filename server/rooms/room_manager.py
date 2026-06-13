"""
Room Manager — Creates, tracks, and destroys game rooms.

Acts as the central registry for all active rooms and provides
lookup and lifecycle operations.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Coroutine

from server.rooms.room import Room, RoomState
from server.rooms.player_session import PlayerSession

logger = logging.getLogger(__name__)

# Type alias for the send callback
SendCallback = Callable[[int, dict[str, Any]], Coroutine[Any, Any, None]]


class RoomManager:
    """
    Manages all active game rooms.

    Provides room creation, lookup by ID or player, and cleanup.
    """

    def __init__(self, send_callback: SendCallback) -> None:
        self._rooms: dict[str, Room] = {}
        self._player_room: dict[int, str] = {}  # player_id → room_id
        self._send_callback: SendCallback = send_callback

    # ----- Room creation -----

    def create_room(self, player_ids: list[int], sessions: dict[int, PlayerSession]) -> Room:
        """
        Create a new room with the given players.

        Args:
            player_ids: List of player IDs to add.
            sessions:   Player session map (for names).

        Returns:
            The newly created Room.
        """
        room_id = f"room_{uuid.uuid4().hex[:8]}"
        room = Room(room_id=room_id)
        room.set_send_callback(self._send_callback)
        room.set_finish_callback(self._on_room_finished)

        for pid in player_ids:
            name = sessions[pid].name if pid in sessions else f"Player {pid}"
            room.add_player(pid, name)
            self._player_room[pid] = room_id

        self._rooms[room_id] = room
        logger.info(
            "Created room %s with players %s",
            room_id,
            player_ids,
        )
        return room

    # ----- Lookups -----

    def get_room(self, room_id: str) -> Room | None:
        """Get a room by its ID."""
        return self._rooms.get(room_id)

    def get_player_room(self, player_id: int) -> Room | None:
        """Get the room a player is currently in."""
        room_id = self._player_room.get(player_id)
        if room_id:
            return self._rooms.get(room_id)
        return None

    @property
    def active_rooms(self) -> int:
        """Number of currently active rooms."""
        return len(self._rooms)

    # ----- Player removal -----

    async def remove_player_from_room(self, player_id: int) -> None:
        """Remove a player from their current room."""
        room_id = self._player_room.pop(player_id, None)
        if room_id is None:
            return

        room = self._rooms.get(room_id)
        if room is None:
            return

        room.remove_player(player_id)
        logger.info("Removed player %d from room %s", player_id, room_id)

        # If room is empty or has too few players during game, destroy it
        if room.player_count == 0:
            await self._destroy_room(room_id)

    # ----- Cleanup -----

    async def _on_room_finished(self, room_id: str) -> None:
        """Called when a room's match ends."""
        # Remove player→room mappings
        room = self._rooms.get(room_id)
        if room:
            for pid in list(room.player_ids):
                self._player_room.pop(pid, None)

        # Schedule cleanup after a short delay so clients can receive final messages
        await self._destroy_room(room_id)

    async def _destroy_room(self, room_id: str) -> None:
        """Destroy a room and clean up all references."""
        room = self._rooms.pop(room_id, None)
        if room:
            # Clean up player mappings
            for pid in list(room.player_ids):
                self._player_room.pop(pid, None)
            await room.destroy()

    async def shutdown(self) -> None:
        """Destroy all rooms (server shutdown)."""
        for room_id in list(self._rooms.keys()):
            await self._destroy_room(room_id)
