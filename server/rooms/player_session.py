"""
Player Session — Represents a connected player's server-side state.

Each connected client gets a PlayerSession that tracks their player ID,
connection state, and the room they are currently in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class PlayerState(Enum):
    """Lifecycle states for a player session."""
    CONNECTED = auto()
    IN_QUEUE = auto()
    IN_ROOM = auto()
    IN_GAME = auto()
    DISCONNECTED = auto()


@dataclass
class PlayerSession:
    """
    Server-side representation of a connected player.

    Attributes:
        player_id:  Unique ID assigned by the ConnectionManager.
        state:      Current lifecycle state.
        room_id:    ID of the room the player is in (or None).
        name:       Display name (auto-generated if not provided).
    """
    player_id: int
    state: PlayerState = PlayerState.CONNECTED
    room_id: str | None = None
    name: str = ""

    def __post_init__(self) -> None:
        if not self.name:
            self.name = f"Player {self.player_id}"
