"""
Movement System — Moves snakes each tick.

Handles smooth turning and continuous forward movement along the
snake's current direction.
"""

from __future__ import annotations

import math

from server.shared.constants import (
    SNAKE_SEGMENT_SPACING,
    SNAKE_TURN_RATE,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from server.simulation.entities.snake import Snake
from server.simulation.entities.snake_segment import SnakeSegment


class MovementSystem:
    """
    Moves all alive snakes forward along their direction each tick.

    Implements smooth turning: the snake's actual direction gradually
    rotates toward ``target_direction`` at ``SNAKE_TURN_RATE`` degrees/s.
    """

    def update(self, snakes: list[Snake], dt: float) -> None:
        """
        Move all alive snakes forward.

        Args:
            snakes: All snakes in the world.
            dt:     Time step in seconds.
        """
        for snake in snakes:
            if not snake.alive:
                continue
            self._turn(snake, dt)
            self._move_forward(snake, dt)

    @staticmethod
    def _turn(snake: Snake, dt: float) -> None:
        """Smoothly rotate direction toward target_direction."""
        diff = snake.target_direction - snake.direction

        # Normalize to [-180, 180]
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        max_turn = SNAKE_TURN_RATE * dt
        if abs(diff) <= max_turn:
            snake.direction = snake.target_direction
        elif diff > 0:
            snake.direction += max_turn
        else:
            snake.direction -= max_turn

        # Normalize direction to [0, 360)
        snake.direction %= 360

    @staticmethod
    def _move_forward(snake: Snake, dt: float) -> None:
        """Move the snake head forward and update body segments."""
        angle_rad = math.radians(snake.direction)
        distance = snake.speed * dt

        # Move head
        snake.x += math.cos(angle_rad) * distance
        snake.y += math.sin(angle_rad) * distance

        # Insert new head segment
        snake.segments.appendleft(SnakeSegment(snake.x, snake.y))

        # Trim tail to maintain length
        while len(snake.segments) > snake.length:
            snake.segments.pop()
