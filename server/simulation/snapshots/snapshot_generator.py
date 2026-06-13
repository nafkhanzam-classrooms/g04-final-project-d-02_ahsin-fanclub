"""
Snapshot Generator — Generates the world state dict for broadcasting.

Creates the snapshot format expected by the client's interpolation system.
"""

from __future__ import annotations

from typing import Any

from server.simulation.entities.snake import Snake
from server.simulation.entities.food import Food


class SnapshotGenerator:
    """
    Generates world state snapshots for client consumption.

    Output format matches what the client's SnapshotInterpolator expects::

        {
            "type": "snapshot",
            "tick": 1234,
            "time_left": 87,
            "snakes": [...],
            "foods": [...]
        }
    """

    def generate(
        self,
        tick: int,
        time_left: int,
        snakes: list[Snake],
        foods: list[Food],
    ) -> dict[str, Any]:
        """
        Generate a snapshot dict.

        Args:
            tick:       Current simulation tick number.
            time_left:  Seconds remaining in the match.
            snakes:     All snake entities.
            foods:      All food entities.

        Returns:
            A dict ready for msgpack encoding and broadcasting.
        """
        return {
            "type": "snapshot",
            "tick": tick,
            "time_left": time_left,
            "snakes": [s.to_snapshot_dict() for s in snakes],
            "foods": [f.to_snapshot_dict() for f in foods],
        }
