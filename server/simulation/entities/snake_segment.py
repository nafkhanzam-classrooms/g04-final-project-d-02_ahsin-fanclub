"""
Snake Segment — A single segment of a snake's body.

Segments track their position in world coordinates and are stored
as a deque for efficient head-insertion and tail-removal during movement.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class SnakeSegment:
    """A single body segment of a snake."""
    x: float
    y: float
