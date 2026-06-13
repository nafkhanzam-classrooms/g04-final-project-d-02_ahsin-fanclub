"""
Collision System — Detects collisions between snakes and boundaries.

Detects:
1. Snake head vs other snake body segments.
2. Snake head vs world boundary.

Does NOT handle the consequences (elimination) — just reports which
snakes should die.
"""

from __future__ import annotations

import math

from server.shared.constants import (
    SNAKE_BODY_RADIUS,
    SNAKE_HEAD_RADIUS,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from server.simulation.entities.snake import Snake


class CollisionSystem:
    """
    Detects collisions and returns the set of player IDs that should die.

    Two collision checks per tick:
    - Boundary: head leaves the world rectangle.
    - Snake-vs-snake: head touches another snake's body segments.
    """

    def check_collisions(self, snakes: list[Snake]) -> set[int]:
        """
        Check all alive snakes for collisions.

        Returns:
            Set of player_ids that collided this tick.
        """
        dead: set[int] = set()

        alive_snakes = [s for s in snakes if s.alive]

        for snake in alive_snakes:
            # Boundary check
            if self._check_boundary(snake):
                dead.add(snake.player_id)
                continue

            # Head-vs-body check against other snakes
            for other in alive_snakes:
                if other.player_id == snake.player_id:
                    continue
                if self._check_head_vs_body(snake, other):
                    dead.add(snake.player_id)
                    break

        return dead

    @staticmethod
    def _check_boundary(snake: Snake) -> bool:
        """Check if the snake head is outside the world boundary."""
        margin = SNAKE_HEAD_RADIUS
        return (
            snake.x < margin
            or snake.x > WORLD_WIDTH - margin
            or snake.y < margin
            or snake.y > WORLD_HEIGHT - margin
        )

    @staticmethod
    def _check_head_vs_body(snake: Snake, other: Snake) -> bool:
        """
        Check if *snake*'s head overlaps any body segment of *other*.

        Skips the first segment (other's head) to avoid head-on
        issues being double-counted.
        """
        collision_dist = SNAKE_HEAD_RADIUS + SNAKE_BODY_RADIUS
        collision_dist_sq = collision_dist * collision_dist

        hx, hy = snake.x, snake.y

        # Skip the other snake's head segment (index 0)
        for i, seg in enumerate(other.segments):
            if i == 0:
                continue
            dx = hx - seg.x
            dy = hy - seg.y
            if dx * dx + dy * dy <= collision_dist_sq:
                return True

        return False
