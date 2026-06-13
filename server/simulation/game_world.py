"""
Game World — The authoritative game simulation.

This is the public API that the networking layer uses to interact with
the game simulation.  It composes all sub-systems (movement, collision,
food, scoring, elimination, timer, win-condition) and drives the
tick-by-tick update loop.
"""

from __future__ import annotations

import math
import random
from typing import Any

from server.shared.constants import (
    SNAKE_INITIAL_LENGTH,
    WORLD_HEIGHT,
    WORLD_WIDTH,
)
from server.simulation.entities.food import Food
from server.simulation.entities.player import Player
from server.simulation.entities.snake import Snake
from server.simulation.snapshots.snapshot_generator import SnapshotGenerator
from server.simulation.systems.collision_system import CollisionSystem
from server.simulation.systems.elimination_system import EliminationSystem
from server.simulation.systems.food_system import FoodSystem
from server.simulation.systems.movement_system import MovementSystem
from server.simulation.systems.scoring_system import ScoringSystem
from server.simulation.systems.timer_system import TimerSystem
from server.simulation.systems.win_condition_system import WinConditionSystem


class GameWorld:
    """
    Authoritative game simulation (GameSimulation interface).

    Public API used by the networking layer::

        world = GameWorld()
        world.add_player(player_id, name)
        world.initialize()
        world.receive_input(player_id, direction)
        world.update(dt)
        snapshot = world.get_snapshot()
    """

    def __init__(self) -> None:
        self._players: dict[int, Player] = {}
        self._tick: int = 0

        # Sub-systems (composed, not inherited)
        self._movement: MovementSystem = MovementSystem()
        self._collision: CollisionSystem = CollisionSystem()
        self._food: FoodSystem = FoodSystem()
        self._scoring: ScoringSystem = ScoringSystem()
        self._elimination: EliminationSystem = EliminationSystem(self._food)
        self._timer: TimerSystem = TimerSystem()
        self._win_condition: WinConditionSystem = WinConditionSystem(self._timer)
        self._snapshot_gen: SnapshotGenerator = SnapshotGenerator()

    # ----- Player management -----

    def add_player(self, player_id: int, name: str = "") -> None:
        """
        Add a player to the simulation.

        The snake is spawned at a random position inside the world.
        """
        if player_id in self._players:
            return

        # Spawn position: random, away from edges
        margin = 200.0
        x = random.uniform(margin, WORLD_WIDTH - margin)
        y = random.uniform(margin, WORLD_HEIGHT - margin)
        direction = random.uniform(0, 360)

        snake = Snake(
            player_id=player_id,
            x=x,
            y=y,
            direction=direction,
            target_direction=direction,
            name=name or f"Player {player_id}",
        )

        self._players[player_id] = Player(
            player_id=player_id,
            snake=snake,
            name=name or f"Player {player_id}",
        )

    def remove_player(self, player_id: int) -> None:
        """Remove a player and their snake from the simulation."""
        player = self._players.pop(player_id, None)
        if player and player.snake.alive:
            self._elimination.eliminate(player.snake)

    # ----- Input -----

    def receive_input(self, player_id: int, direction: float) -> None:
        """
        Receive a direction input from a player.

        The direction is stored and applied during the next tick.
        """
        player = self._players.get(player_id)
        if player and player.snake.alive:
            player.snake.target_direction = direction

    # ----- Simulation tick -----

    def initialize(self) -> None:
        """Initialize the world (spawn food, reset timer)."""
        self._food.initialize()
        self._timer.reset()
        self._tick = 0

    def update(self, dt: float) -> None:
        """
        Advance the simulation by one tick.

        Order of operations:
        1. Move snakes
        2. Detect food consumption
        3. Update scores
        4. Detect collisions
        5. Handle eliminations
        6. Maintain food count
        7. Update timer
        8. Increment tick
        """
        snakes = self._get_all_snakes()

        # 1. Movement
        self._movement.update(snakes, dt)

        # 2. Food consumption
        consumed = self._food.check_consumption(snakes)
        for player_id, food in consumed:
            player = self._players.get(player_id)
            if player:
                # 3. Score update
                self._scoring.apply_food_eaten(player.snake)

        # 4. Collision detection
        dead_ids = self._collision.check_collisions(snakes)
        for dead_id in dead_ids:
            player = self._players.get(dead_id)
            if player:
                # 5. Elimination
                self._elimination.eliminate(player.snake)

        # 6. Maintain food count
        self._food.maintain_count()

        # 7. Timer
        self._timer.update(dt)

        # 8. Tick counter
        self._tick += 1

    # ----- Queries -----

    def get_snapshot(self) -> dict[str, Any]:
        """Generate a world state snapshot for broadcasting."""
        return self._snapshot_gen.generate(
            tick=self._tick,
            time_left=self._timer.time_left,
            snakes=self._get_all_snakes(),
            foods=self._food.foods,
        )

    def get_pending_eliminations(self) -> list[int]:
        """Return and clear the list of player IDs eliminated this tick."""
        return self._elimination.drain_eliminations()

    def check_win_condition(self) -> dict[str, Any] | None:
        """Check if the match should end. Returns result dict or None."""
        return self._win_condition.check(self._get_all_snakes())

    # ----- Private -----

    def _get_all_snakes(self) -> list[Snake]:
        """Get a list of all snake entities."""
        return [p.snake for p in self._players.values()]
