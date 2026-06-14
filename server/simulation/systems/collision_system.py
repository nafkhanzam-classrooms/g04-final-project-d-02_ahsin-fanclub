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
            if self._check_boundary(snake):
                dead.add(snake.player_id)
                continue

            for other in alive_snakes:
                if other.player_id == snake.player_id:
                    continue
                if self._check_head_vs_body(snake, other):
                    dead.add(snake.player_id)
                    break

        for i, snake_a in enumerate(alive_snakes):
            if snake_a.player_id in dead:
                continue
            for snake_b in alive_snakes[i + 1:]:
                if snake_b.player_id in dead:
                    continue
                if self._check_head_vs_head(snake_a, snake_b):
                    dead.add(snake_a.player_id)
                    dead.add(snake_b.player_id)

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

        for i, seg in enumerate(other.segments):
            if i == 0:
                continue
            dx = hx - seg.x
            dy = hy - seg.y
            if dx * dx + dy * dy <= collision_dist_sq:
                return True

        return False

    @staticmethod
    def _check_head_vs_head(a: Snake, b: Snake) -> bool:
        """
        Both snakes die on head-on collision (mutual kill policy).
        Uses SNAKE_HEAD_RADIUS * 2 as the collision distance since
        both entities are heads.
        """
        collision_dist = SNAKE_HEAD_RADIUS * 2
        collision_dist_sq = collision_dist * collision_dist
        dx = a.x - b.x
        dy = a.y - b.y
        return dx * dx + dy * dy <= collision_dist_sq
