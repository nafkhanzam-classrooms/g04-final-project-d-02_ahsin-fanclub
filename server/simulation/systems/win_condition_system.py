"""
Win Condition System — Determines when a match ends and who won.

Match ends when:
A) Only one snake remains alive → that snake wins.
B) Timer expires → highest score wins.
"""

from __future__ import annotations

from typing import Any

from server.simulation.entities.snake import Snake
from server.simulation.systems.timer_system import TimerSystem


class WinConditionSystem:
    """
    Checks win conditions each tick.

    Returns a result dict when the match should end, or None if it continues.
    """

    def __init__(self, timer: TimerSystem) -> None:
        self._timer: TimerSystem = timer

    def check(self, snakes: list[Snake]) -> dict[str, Any] | None:
        """
        Check if the match should end.

        Returns:
            A result dict with ``winner_id``, ``winner_name``, and
            ``rankings`` if the match ends, otherwise None.
        """
        if not snakes:
            return None

        alive = [s for s in snakes if s.alive]

        if len(alive) <= 1 and len(snakes) > 1:
            if len(alive) == 1:
                winner = alive[0]
            else:
                winner = max(snakes, key=lambda s: s.score)

            return self._build_result(winner, snakes)

        if self._timer.expired:
            if alive:
                winner = max(alive, key=lambda s: s.score)
            else:
                winner = max(snakes, key=lambda s: s.score)
            return self._build_result(winner, snakes)

        return None

    @staticmethod
    def _build_result(winner: Snake, snakes: list[Snake]) -> dict[str, Any]:
        """Build the match result payload."""
        sorted_snakes = sorted(snakes, key=lambda s: s.score, reverse=True)
        rankings = [
            {
                "id": s.player_id,
                "name": s.name,
                "score": s.score,
            }
            for s in sorted_snakes
        ]

        return {
            "winner_id": winner.player_id,
            "winner_name": winner.name,
            "rankings": rankings,
        }
