"""
Player — Server-side player record for the simulation.

Links a player ID to their snake entity.
"""

from __future__ import annotations

from dataclasses import dataclass

from server.simulation.entities.snake import Snake


@dataclass
class Player:
    """
    A player in the simulation.

    Attributes:
        player_id:  Unique player ID.
        snake:      The player's snake entity.
        name:       Display name.
    """
    player_id: int
    snake: Snake
    name: str = ""
