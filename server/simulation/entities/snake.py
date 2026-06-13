"""
Snake — Server-authoritative snake entity.

The snake stores its position, direction, body segments, and state.
Movement and growth are managed by the systems layer.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

from server.shared.constants import (
    SNAKE_BASE_SPEED,
    SNAKE_INITIAL_LENGTH,
    SNAKE_SEGMENT_SPACING,
)
from server.simulation.entities.snake_segment import SnakeSegment


@dataclass
class Snake:
    """
    Server-authoritative snake entity.

    Attributes:
        player_id:     Owner player ID.
        x:             Head X position (world coordinates).
        y:             Head Y position (world coordinates).
        direction:     Current heading angle in degrees (0 = right).
        target_direction: The direction the player wants to face.
        speed:         Movement speed (units per second).
        length:        Target body length in segments.
        score:         Current score.
        alive:         Whether the snake is alive.
        segments:      Deque of body segments (head at front).
        name:          Player display name.
    """
    player_id: int
    x: float = 0.0
    y: float = 0.0
    direction: float = 0.0
    target_direction: float = 0.0
    speed: float = SNAKE_BASE_SPEED
    length: int = SNAKE_INITIAL_LENGTH
    score: int = 0
    alive: bool = True
    segments: deque[SnakeSegment] = field(default_factory=deque)
    name: str = ""

    def __post_init__(self) -> None:
        """Build initial segments behind the head."""
        if not self.segments:
            self._build_initial_segments()

    def _build_initial_segments(self) -> None:
        """Generate initial body segments trailing behind the head."""
        self.segments.clear()
        self.segments.append(SnakeSegment(self.x, self.y))

        angle_rad = math.radians(self.direction + 180)
        for i in range(1, self.length):
            prev = self.segments[-1]
            sx = prev.x + math.cos(angle_rad) * SNAKE_SEGMENT_SPACING
            sy = prev.y + math.sin(angle_rad) * SNAKE_SEGMENT_SPACING
            self.segments.append(SnakeSegment(sx, sy))

    @property
    def head(self) -> SnakeSegment:
        """The head segment (first in the deque)."""
        return self.segments[0]

    def to_snapshot_dict(self) -> dict:
        """Convert to a dict suitable for snapshot broadcasting."""
        return {
            "id": self.player_id,
            "x": round(self.x, 1),
            "y": round(self.y, 1),
            "length": self.length,
            "score": self.score,
            "alive": self.alive,
            "name": self.name,
        }
