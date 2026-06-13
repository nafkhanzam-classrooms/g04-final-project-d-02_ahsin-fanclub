"""
Food — A static food item in the game world.
"""

from __future__ import annotations

from dataclasses import dataclass

from server.shared.constants import FOOD_RADIUS


@dataclass
class Food:
    """
    A food item in the arena.

    Attributes:
        x:      World X position.
        y:      World Y position.
        radius: Collision / visual radius.
    """
    x: float
    y: float
    radius: float = FOOD_RADIUS

    def to_snapshot_dict(self) -> dict:
        """Convert to a dict suitable for snapshot broadcasting."""
        return {
            "x": round(self.x, 1),
            "y": round(self.y, 1),
        }
