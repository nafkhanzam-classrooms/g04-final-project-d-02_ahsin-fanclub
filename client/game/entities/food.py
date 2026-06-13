"""
Food entity — Pure data class representing a food item on the arena.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FoodData:
    """
    A single food item in the game world.

    Attributes:
        x:     World X position.
        y:     World Y position.
        radius: Visual radius for rendering.
        color:  RGB tuple for rendering (randomized per item).
    """
    x: float = 0.0
    y: float = 0.0
    radius: float = 5.0
    color: tuple[int, int, int] = (255, 100, 100)

    @staticmethod
    def from_server(data: dict) -> "FoodData":
        """Construct a FoodData from a server snapshot dict entry."""
        return FoodData(
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
        )
