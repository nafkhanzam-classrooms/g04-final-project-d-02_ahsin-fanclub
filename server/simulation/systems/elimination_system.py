from __future__ import annotations

from server.shared.constants import DEATH_FOOD_RATIO
from server.simulation.entities.snake import Snake
from server.simulation.systems.food_system import FoodSystem


class EliminationSystem:
    """
    Processes snake eliminations.
    """

    def __init__(self, food_system: FoodSystem) -> None:
        self._food_system: FoodSystem = food_system
        self._pending_eliminations: list[int] = []

    @property
    def pending_eliminations(self) -> list[int]:
        """Player IDs eliminated since last drain."""
        return self._pending_eliminations

    def drain_eliminations(self) -> list[int]:
        """Return and clear pending eliminations."""
        result = list(self._pending_eliminations)
        self._pending_eliminations.clear()
        return result

    def eliminate(self, snake: Snake) -> None:
        """
        Eliminate a snake.

        Marks it dead, converts segments to food, and records the event.
        """
        if not snake.alive:
            return

        snake.alive = False
        self._pending_eliminations.append(snake.player_id)

        # Convert body segments to food
        segment_positions = [(seg.x, seg.y) for seg in snake.segments]
        if segment_positions:
            self._food_system.spawn_death_food(segment_positions, DEATH_FOOD_RATIO)
