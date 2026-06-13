"""
Event types for the internal server event bus.

Each event is a simple frozen dataclass so it is hashable and immutable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PlayerJoinedQueue:
    """A player requested to join the matchmaking queue."""
    player_id: int


@dataclass(frozen=True)
class PlayerLeftQueue:
    """A player cancelled their matchmaking request."""
    player_id: int


@dataclass(frozen=True)
class MatchCreated:
    """A new match room has been allocated."""
    room_id: str
    player_ids: tuple[int, ...]


@dataclass(frozen=True)
class MatchStarted:
    """A match has started (countdown finished)."""
    room_id: str


@dataclass(frozen=True)
class PlayerDisconnected:
    """A player disconnected from the server."""
    player_id: int


@dataclass(frozen=True)
class PlayerEliminated:
    """A player's snake was eliminated in-game."""
    room_id: str
    player_id: int


@dataclass(frozen=True)
class MatchEnded:
    """A match has concluded."""
    room_id: str
    winner_id: int
