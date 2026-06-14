"""
Snake entity — Pure data class representing a snake's visual state.

This is NOT the authoritative game state.  It holds the data needed
by the renderer to draw a snake on screen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


@dataclass
class SnakeSegment:
    """A single segment (body part) of a snake."""
    x: float
    y: float


@dataclass
class SnakeData:
    """
    Complete visual state of a snake as received from the server
    (plus interpolated positions).

    Attributes:
        id:        Unique player/snake ID assigned by the server.
        x:         Head X position (world coordinates).
        y:         Head Y position (world coordinates).
        length:    Current length in segments.
        score:     Current score.
        alive:     Whether this snake is still in play.
        direction: Current heading angle in degrees (0 = right).
        segments:  Body segment positions (head at index 0).
        color:     RGB tuple for rendering.
        name:      Player display name.
    """
    id: int = 0
    x: float = 0.0
    y: float = 0.0
    length: int = 5
    score: int = 0
    alive: bool = True
    direction: float = 0.0
    segments: list[SnakeSegment] = field(default_factory=list)
    color: tuple[int, int, int] = (0, 200, 100)
    name: str = ""

    def head_position(self) -> tuple[float, float]:
        """Return the head position as a tuple."""
        return (self.x, self.y)

    @staticmethod
    def from_server(data: dict) -> "SnakeData":
        """
        Construct a SnakeData from a server snapshot dict entry.

        Expected keys: id, x, y, length, score, alive
        """
        segments = [
            SnakeSegment(float(seg.get("x", 0.0)), float(seg.get("y", 0.0)))
            for seg in data.get("segments", [])
        ]

        return SnakeData(
            id=data.get("id", 0),
            x=float(data.get("x", 0)),
            y=float(data.get("y", 0)),
            length=data.get("length", 5),
            score=data.get("score", 0),
            alive=data.get("alive", True),
            direction=float(data.get("direction", 0.0)),
            segments=segments,
            name=data.get("name", ""),
        )

    def build_segments(self) -> None:
        """
        Rebuild the segment list based on the head position and direction.

        In a real scenario, segment positions come from the server or from
        interpolated history.  This is a fallback for rendering when the
        server only sends the head position.
        """
        if self.segments:
            return

        segment_spacing = 8.0
        self.segments = [SnakeSegment(self.x, self.y)]

        angle_rad = math.radians(self.direction + 180)
        for i in range(1, self.length):
            prev = self.segments[i - 1]
            sx = prev.x + math.cos(angle_rad) * segment_spacing
            sy = prev.y + math.sin(angle_rad) * segment_spacing
            self.segments.append(SnakeSegment(sx, sy))
