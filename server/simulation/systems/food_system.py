"""
Food System — Manages food spawning and consumption.

Maintains the target food count by spawning replacements and handles
food-snake proximity detection for consumption events.
"""

from __future__ import annotations

import random

from server.shared.constants import (
    FOOD_RADIUS,
    SNAKE_HEAD_RADIUS,
    TARGET_FOOD_COUNT,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from server.simulation.entities.food import Food
from server.simulation.entities.snake import Snake


class FoodSystem:
    """
    Handles food lifecycle: spawning, consumption detection, and count maintenance.
    """

    def __init__(self) -> None:
        self._foods: list[Food] = []

    @property
    def foods(self) -> list[Food]:
        """Current food items in the world."""
        return self._foods

    def initialize(self) -> None:
        """Spawn initial food to fill the world."""
        self._foods.clear()
        for _ in range(TARGET_FOOD_COUNT):
            self._foods.append(self._spawn_food())

    def check_consumption(self, snakes: list[Snake]) -> list[tuple[int, Food]]:
        """
        Check if any alive snake's head is close enough to eat food.

        Returns:
            List of (player_id, Food) tuples for consumed food items.
        """
        consumed: list[tuple[int, Food]] = []
        eat_dist = SNAKE_HEAD_RADIUS + FOOD_RADIUS
        eat_dist_sq = eat_dist * eat_dist

        alive = [s for s in snakes if s.alive]

        remaining: list[Food] = []
        for food in self._foods:
            eaten = False
            for snake in alive:
                dx = snake.x - food.x
                dy = snake.y - food.y
                if dx * dx + dy * dy <= eat_dist_sq:
                    consumed.append((snake.player_id, food))
                    eaten = True
                    break
            if not eaten:
                remaining.append(food)

        self._foods = remaining
        return consumed

    def maintain_count(self) -> None:
        """Spawn replacement food to maintain TARGET_FOOD_COUNT."""
        deficit = TARGET_FOOD_COUNT - len(self._foods)
        for _ in range(deficit):
            self._foods.append(self._spawn_food())

    def spawn_death_food(self, segments: list[tuple[float, float]], ratio: float = 0.5) -> None:
        """
        Spawn food at some of a dead snake's segment positions.

        Args:
            segments: List of (x, y) segment positions.
            ratio:    Fraction of segments to convert to food.
        """
        count = max(1, int(len(segments) * ratio))
        chosen = random.sample(segments, min(count, len(segments)))
        for x, y in chosen:
            self._foods.append(Food(x=x, y=y))

    @staticmethod
    def _spawn_food() -> Food:
        """Spawn a food item at a random world position (with margin)."""
        margin = 50.0
        return Food(
            x=random.uniform(margin, WORLD_WIDTH - margin),
            y=random.uniform(margin, WORLD_HEIGHT - margin),
        )
