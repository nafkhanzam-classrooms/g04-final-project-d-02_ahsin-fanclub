"""
Snapshot Interpolator — Smooth rendering between server ticks.

The server sends state snapshots at ~30 Hz.  The client renders at 60 FPS.
This module interpolates entity positions between two bracketing snapshots
so movement appears fluid, even when packets are delayed or jittery.

=== Algorithm ===

1. Each incoming snapshot is timestamped with `time.monotonic()` and
   pushed into the SnapshotBuffer.

2. The renderer asks for the interpolated state at:
       render_time = now - INTERP_DELAY

   The delay (default 100 ms ≈ 3 server ticks at 30 Hz) ensures we almost
   always have two snapshots to interpolate between, absorbing jitter.

3. We find the two snapshots A and B that bracket render_time:
       A.local_time ≤ render_time ≤ B.local_time

4. Compute the blend factor:
       alpha = (render_time - A.time) / (B.time - A.time)   clamped [0, 1]

5. For each entity present in BOTH snapshots, linearly interpolate:
       x = A.x + (B.x - A.x) * alpha
       y = A.y + (B.y - A.y) * alpha

6. Edge cases:
   - Only one snapshot available → use it directly (no interpolation).
   - Entity in B but not A → snap to B's position (newly spawned).
   - Entity in A but not B → keep A's last position or remove.
   - render_time beyond the latest snapshot → hold the last known state
     (avoids extrapolation artefacts).

7. The LOCAL player's snake uses client-side prediction: we immediately
   apply direction changes and reconcile on the next server snapshot,
   so input feels instantaneous.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from game.entities.food import FoodData
from game.entities.snake import SnakeData
from game.networking.snapshot_buffer import SnapshotBuffer


# Default interpolation delay in seconds (100 ms)
INTERP_DELAY: float = 0.100


@dataclass
class InterpolatedState:
    """The result of interpolation — ready to be rendered."""
    snakes: list[SnakeData] = field(default_factory=list)
    foods: list[FoodData] = field(default_factory=list)
    time_left: int = 0
    local_player_id: int = -1
    tick: int = 0


class SnapshotInterpolator:
    """
    Interpolates between buffered server snapshots for smooth 60 FPS rendering.

    Usage:
        interpolator = SnapshotInterpolator()

        # When a snapshot arrives from the network:
        interpolator.push_snapshot(snapshot_data)

        # Every render frame:
        state = interpolator.get_interpolated_state()
    """

    def __init__(self, interp_delay: float = INTERP_DELAY) -> None:
        self._buffer: SnapshotBuffer = SnapshotBuffer(max_size=30)
        self._interp_delay: float = interp_delay

        # Client-side prediction state for local player
        self._predicted_direction: float | None = None
        self._local_player_id: int = -1

    @property
    def buffer(self) -> SnapshotBuffer:
        """Expose the underlying snapshot buffer (read-only intent)."""
        return self._buffer

    def push_snapshot(self, snapshot_data: dict[str, Any]) -> None:
        """Add a new server snapshot to the buffer."""
        self._buffer.push(snapshot_data)

        # Track the local player ID
        if "local_player_id" in snapshot_data:
            self._local_player_id = snapshot_data["local_player_id"]

    def set_predicted_direction(self, direction: float) -> None:
        """
        Set the local player's predicted direction for client-side prediction.
        This will be applied to the local snake's rendering until the server
        confirms or corrects.
        """
        self._predicted_direction = direction

    def get_interpolated_state(self) -> InterpolatedState:
        """
        Compute the interpolated game state for the current render frame.

        Returns an InterpolatedState with entity positions blended between
        the two closest server snapshots.
        """
        render_time = time.monotonic() - self._interp_delay
        a, b = self._buffer.get_bracketing(render_time)

        if a is None:
            # No data at all
            return InterpolatedState()

        if b is None:
            # Only one snapshot — use it directly
            return self._state_from_snapshot(a.data)

        # Compute blend factor
        time_span = b.local_time - a.local_time
        if time_span <= 0:
            alpha = 1.0
        else:
            alpha = (render_time - a.local_time) / time_span
            alpha = max(0.0, min(1.0, alpha))

        return self._interpolate(a.data, b.data, alpha)

    def clear(self) -> None:
        """Reset the interpolator state."""
        self._buffer.clear()
        self._predicted_direction = None

    # ----- Private helpers -----

    def _state_from_snapshot(self, data: dict[str, Any]) -> InterpolatedState:
        """Build an InterpolatedState from a single snapshot (no blending)."""
        snakes = [
            SnakeData.from_server(s) for s in data.get("snakes", [])
        ]
        foods = [
            FoodData.from_server(f) for f in data.get("foods", [])
        ]

        # Apply client-side prediction to local snake
        self._apply_prediction(snakes)

        # Build segments for rendering
        for snake in snakes:
            snake.build_segments()

        return InterpolatedState(
            snakes=snakes,
            foods=foods,
            time_left=data.get("time_left", 0),
            local_player_id=data.get("local_player_id", -1),
            tick=data.get("tick", 0),
        )

    def _interpolate(
        self,
        data_a: dict[str, Any],
        data_b: dict[str, Any],
        alpha: float,
    ) -> InterpolatedState:
        """Interpolate between two snapshots at blend factor *alpha*."""
        snakes_a = {s["id"]: s for s in data_a.get("snakes", [])}
        snakes_b = {s["id"]: s for s in data_b.get("snakes", [])}

        # Merge snake IDs from both snapshots
        all_ids = set(snakes_a.keys()) | set(snakes_b.keys())
        snakes: list[SnakeData] = []

        for sid in all_ids:
            sa = snakes_a.get(sid)
            sb = snakes_b.get(sid)

            if sa and sb:
                # Interpolate position
                snake = SnakeData(
                    id=sid,
                    x=sa["x"] + (sb["x"] - sa["x"]) * alpha,
                    y=sa["y"] + (sb["y"] - sa["y"]) * alpha,
                    length=sb.get("length", sa.get("length", 5)),
                    score=sb.get("score", sa.get("score", 0)),
                    alive=sb.get("alive", True),
                    name=sb.get("name", sa.get("name", "")),
                )
            elif sb:
                # New snake — snap to B
                snake = SnakeData.from_server(sb)
            else:
                # Snake only in A (possibly dead / disconnected) — use A
                assert sa is not None
                snake = SnakeData.from_server(sa)

            snakes.append(snake)

        # Interpolate foods — foods don't move, just use snapshot B
        foods = [FoodData.from_server(f) for f in data_b.get("foods", [])]

        # Apply prediction to local snake
        self._apply_prediction(snakes)

        # Build segments
        for snake in snakes:
            snake.build_segments()

        return InterpolatedState(
            snakes=snakes,
            foods=foods,
            time_left=data_b.get("time_left", data_a.get("time_left", 0)),
            local_player_id=data_b.get(
                "local_player_id",
                data_a.get("local_player_id", -1),
            ),
            tick=data_b.get("tick", data_a.get("tick", 0)),
        )

    def _apply_prediction(self, snakes: list[SnakeData]) -> None:
        """
        Apply client-side prediction to the local player's snake.

        If the player has changed direction locally but the server hasn't
        confirmed yet, we use the predicted direction for rendering.
        """
        if self._predicted_direction is None:
            return
        for snake in snakes:
            if snake.id == self._local_player_id:
                snake.direction = self._predicted_direction
                break
