"""
Room Manager — Creates, tracks, and destroys game rooms.

Acts as the central registry for all active rooms and provides
lookup and lifecycle operations.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Callable, Coroutine

from server.shared.constants import MAX_PLAYERS_PER_ROOM
from server.rooms.room import Room, RoomState
from server.rooms.player_session import PlayerSession, PlayerState
from server.shared.schemas import RoomPlayer, RoomStatePayload

logger = logging.getLogger(__name__)

# Type alias for the send callback
SendCallback = Callable[[int, dict[str, Any]], Coroutine[Any, Any, None]]


class RoomManager:
    """
    Manages all active game rooms.

    Provides room creation, lookup by ID or player, and cleanup.
    """

    def __init__(self, send_callback: SendCallback, sessions: dict[int, PlayerSession]) -> None:
        self._rooms: dict[str, Room] = {}
        self._player_room: dict[int, str] = {}  # player_id → room_id
        self._send_callback: SendCallback = send_callback
        self._sessions: dict[int, PlayerSession] = sessions

    # ----- Room creation -----

    def _generate_room_code(self) -> str:
        """Generate a unique 6-digit room code."""
        while True:
            room_id = f"{uuid.uuid4().int % 900000 + 100000:06d}"
            if room_id not in self._rooms:
                return room_id

    def create_room(self, player_ids: list[int]) -> Room:
        """
        Create a new room with the given players.

        Args:
            player_ids: List of player IDs to add.

        Returns:
            The newly created Room.
        """
        room_id = self._generate_room_code()
        room = Room(room_id=room_id)
        room.set_send_callback(self._send_callback)
        room.set_finish_callback(self._on_room_finished)

        for pid in player_ids:
            name = self._sessions[pid].name if pid in self._sessions else f"Player {pid}"
            room.add_player(pid, name)
            self._player_room[pid] = room_id
            session = self._sessions.get(pid)
            if session:
                session.room_id = room_id
                session.state = PlayerState.IN_ROOM

        self._rooms[room_id] = room
        logger.info(
            "Created room %s with players %s",
            room_id,
            player_ids,
        )
        return room

    def join_room(self, room_id: str, player_id: int) -> Room | None:
        """Add a player to an existing room if it can accept them."""
        room = self._rooms.get(room_id)
        if room is None:
            return None
        if room.state != RoomState.WAITING:
            return None
        if room.is_full:
            return None
        if player_id in self._player_room:
            return None

        name = self._sessions[player_id].name if player_id in self._sessions else f"Player {player_id}"
        room.add_player(player_id, name)
        self._player_room[player_id] = room_id
        session = self._sessions.get(player_id)
        if session:
            session.room_id = room_id
            session.state = PlayerState.IN_ROOM
        return room

    def leave_room(self, player_id: int) -> Room | None:
        """Remove a player from their current room and return the room."""
        room_id = self._player_room.pop(player_id, None)
        if room_id is None:
            return None
        room = self._rooms.get(room_id)
        if room is None:
            return None
        room.remove_player(player_id)
        session = self._sessions.get(player_id)
        if session:
            session.room_id = None
        return room

    def build_room_state(self, room: Room) -> dict[str, Any]:
        """Build a client-facing room state payload."""
        # instead of relying on player_ids[0] which is fragile.
        host_player_id = room.host_player_id
        players = [
            RoomPlayer(
                player_id=pid,
                name=room._player_names.get(pid, f"Player {pid}"),
                is_host=(pid == host_player_id),
            )
            for pid in room.player_ids
        ]
        can_start = room.state == RoomState.WAITING and len(room.player_ids) >= 1
        return RoomStatePayload(
            room_id=room.room_id,
            state=room.state.name.lower(),
            players=players,
            host_player_id=host_player_id,
            can_start=can_start,
            player_count=room.player_count,
            max_players=MAX_PLAYERS_PER_ROOM,
        ).to_dict()

    async def broadcast_room_state(self, room: Room) -> None:
        """Send the current room state to every player in the room."""
        for pid in list(room.player_ids):
            state = self.build_room_state(room)
            state["local_player_id"] = pid
            await self._send_callback(pid, state)

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
        room = self.leave_room(player_id)
        if room is None:
            return
        logger.info("Removed player %d from room %s", player_id, room.room_id)

        # If room is empty or has too few players during game, destroy it
        if room.player_count == 0:
            await self._destroy_room(room.room_id)
        else:
            await self.broadcast_room_state(room)

    # ----- Cleanup -----

    async def _on_room_finished(self, room_id: str) -> None:
        """Called when a room's match ends."""
        # Remove player→room mappings
        room = self._rooms.get(room_id)
        if room:
            for pid in list(room.player_ids):
                self._player_room.pop(pid, None)
                session = self._sessions.get(pid)
                if session:
                    session.room_id = None

        # Schedule cleanup after a short delay so clients can receive final messages
        await self._destroy_room(room_id)

    async def _destroy_room(self, room_id: str) -> None:
        """Destroy a room and clean up all references."""
        room = self._rooms.pop(room_id, None)
        if room:
            # Clean up player mappings
            for pid in list(room.player_ids):
                self._player_room.pop(pid, None)
                session = self._sessions.get(pid)
                if session:
                    session.room_id = None
            await room.destroy()

    async def shutdown(self) -> None:
        """Destroy all rooms (server shutdown)."""
        for room_id in list(self._rooms.keys()):
            await self._destroy_room(room_id)
