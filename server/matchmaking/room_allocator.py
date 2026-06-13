"""
Room Allocator — Decides how many players go into a room.

Currently uses a simple strategy: when at least MIN_PLAYERS_PER_ROOM
are waiting, create a room with up to MAX_PLAYERS_PER_ROOM players.
"""

from __future__ import annotations

from server.shared.constants import MAX_PLAYERS_PER_ROOM, MIN_PLAYERS_PER_ROOM


class RoomAllocator:
    """
    Determines room sizing based on queue state.

    Can be extended with more sophisticated algorithms (skill-based,
    region-based) in the future.
    """

    def __init__(
        self,
        min_players: int = MIN_PLAYERS_PER_ROOM,
        max_players: int = MAX_PLAYERS_PER_ROOM,
    ) -> None:
        self._min_players: int = min_players
        self._max_players: int = max_players

    def should_create_room(self, queue_size: int) -> bool:
        """Check if there are enough players to create a room."""
        return queue_size >= self._min_players

    def get_room_size(self, queue_size: int) -> int:
        """
        Determine how many players to put in the next room.

        Takes at most max_players, or however many are available
        (capped at max_players).
        """
        return min(queue_size, self._max_players)
