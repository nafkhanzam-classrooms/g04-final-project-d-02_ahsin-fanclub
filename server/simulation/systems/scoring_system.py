"""
Scoring System — Updates snake scores when food is consumed.

Increases both the snake's length and score based on configurable constants.
"""

from __future__ import annotations

from server.shared.constants import FOOD_LENGTH_GAIN, FOOD_SCORE_VALUE
from server.simulation.entities.snake import Snake


class ScoringSystem:
    """
    Updates snake score and length when food is eaten.
    """

    def apply_food_eaten(self, snake: Snake) -> None:
        """
        Apply the effects of eating one food item.

        Args:
            snake: The snake that ate the food.
        """
        snake.score += FOOD_SCORE_VALUE
        snake.length += FOOD_LENGTH_GAIN
