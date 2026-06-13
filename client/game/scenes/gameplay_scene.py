"""
Gameplay Scene — Core game loop: input → network → interpolate → render.

This is where the actual game takes place.  The scene:
  1. Captures mouse input and calculates the direction angle
  2. Sends direction to the server (with threshold-based throttling)
  3. Receives snapshots via the EventDispatcher
  4. Pushes snapshots into the SnapshotInterpolator
  5. Renders the interpolated state through the Renderer
  6. Displays the HUD overlay
"""

from __future__ import annotations

import asyncio
import math
import time
from typing import Any, TYPE_CHECKING

import pygame

from game.entities.snake import SnakeData
from game.networking.protocol import make_input_message
from game.rendering.camera import Camera
from game.rendering.interpolation import InterpolatedState, SnapshotInterpolator
from game.rendering.renderer import Renderer
from game.scene_manager import Scene
from game.ui.hud import HUD

if TYPE_CHECKING:
    from game.game_app import GameApp


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

# Minimum direction change (degrees) before sending a new input to the server
DIRECTION_THRESHOLD: float = 2.0

# Target server update rate (Hz)
INPUT_SEND_RATE: float = 30.0  # Send at most 30 inputs per second
INPUT_SEND_INTERVAL: float = 1.0 / INPUT_SEND_RATE


class GameplayScene(Scene):
    """
    Core gameplay scene.

    Handles input, networking, interpolation, rendering, and HUD display.
    """

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size

        # Rendering components
        self._camera: Camera = Camera(sw, sh, lerp_speed=6.0, dead_zone=20.0)
        self._renderer: Renderer = Renderer(self._camera)
        self._interpolator: SnapshotInterpolator = SnapshotInterpolator()
        self._hud: HUD = HUD(sw, sh)

        # Input state
        self._last_sent_direction: float = 0.0
        self._last_send_time: float = 0.0
        self._current_direction: float = 0.0

        # Game state
        self._state: InterpolatedState = InterpolatedState()
        self._local_alive: bool = True
        self._local_score: int = 0
        self._local_rank: int = 0
        self._total_players: int = 0

        # Performance tracking
        self._fps_counter: int = 0
        self._fps_timer: float = 0.0
        self._current_fps: int = 0

    # ----- Scene lifecycle -----

    def enter(self) -> None:
        """Subscribe to server events and initialize state."""
        dispatcher = self.app.event_dispatcher
        dispatcher.subscribe("snapshot", self._on_snapshot)
        dispatcher.subscribe("player_eliminated", self._on_player_eliminated)
        dispatcher.subscribe("match_end", self._on_match_end)
        dispatcher.subscribe("error", self._on_error)

        self._interpolator.clear()
        self._camera.snap_to_target()

    def exit(self) -> None:
        """Unsubscribe from server events."""
        dispatcher = self.app.event_dispatcher
        dispatcher.unsubscribe("snapshot", self._on_snapshot)
        dispatcher.unsubscribe("player_eliminated", self._on_player_eliminated)
        dispatcher.unsubscribe("match_end", self._on_match_end)
        dispatcher.unsubscribe("error", self._on_error)

    # ----- Event handling -----

    def handle_event(self, event: pygame.event.Event) -> None:
        # No click-based interactions during gameplay
        # (mouse is used exclusively for direction control)
        pass

    # ----- Update -----

    def update(self, dt: float) -> None:
        """Update input, interpolation, camera, and HUD each frame."""
        # --- FPS counter ---
        self._fps_counter += 1
        self._fps_timer += dt
        if self._fps_timer >= 1.0:
            self._current_fps = self._fps_counter
            self._fps_counter = 0
            self._fps_timer -= 1.0

        # --- Interpolation ---
        self._state = self._interpolator.get_interpolated_state()

        # --- Find local snake ---
        local_snake = self._find_local_snake()

        # --- Input: mouse direction ---
        if local_snake and local_snake.alive:
            self._process_input(local_snake, dt)

        # --- Camera follow ---
        if local_snake:
            self._camera.set_target(local_snake.x, local_snake.y)
        self._camera.update(dt)

        # --- Compute rank ---
        self._compute_rank()

        # --- HUD ---
        self._hud.update(
            time_left=self._state.time_left,
            score=self._local_score,
            rank=self._local_rank,
            total_players=self._total_players,
            alive=self._local_alive,
            fps=self._current_fps,
            ping=self.app.network_client.ping_ms,
        )

    # ----- Render -----

    def render(self, screen: pygame.Surface) -> None:
        """Draw the game world and HUD."""
        self._renderer.render_frame(screen, self._state)
        self._hud.render(screen)

    # ----- Input processing -----

    def _process_input(self, local_snake: SnakeData, dt: float) -> None:
        """
        Calculate direction from the snake's head to the mouse cursor.
        Send to server if the change exceeds the threshold and the rate
        limit allows.
        """
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # Convert mouse screen position to world position
        world_mx, world_my = self._camera.screen_to_world(mouse_x, mouse_y)

        # Direction angle from snake head to mouse (in degrees)
        dx = world_mx - local_snake.x
        dy = world_my - local_snake.y
        angle = math.degrees(math.atan2(dy, dx))

        self._current_direction = angle

        # Client-side prediction — immediately update the local snake's direction
        self._interpolator.set_predicted_direction(angle)

        # Check threshold
        angle_diff = abs(self._normalize_angle(angle - self._last_sent_direction))
        now = time.monotonic()
        time_since_last = now - self._last_send_time

        if angle_diff >= DIRECTION_THRESHOLD and time_since_last >= INPUT_SEND_INTERVAL:
            # TODO: SERVER INTEGRATION — Send direction input to server
            asyncio.ensure_future(
                self.app.network_client.send(make_input_message(angle))
            )
            self._last_sent_direction = angle
            self._last_send_time = now

    @staticmethod
    def _normalize_angle(angle: float) -> float:
        """Normalize an angle to the range [-180, 180]."""
        while angle > 180:
            angle -= 360
        while angle < -180:
            angle += 360
        return angle

    # ----- Server event handlers -----

    def _on_snapshot(self, data: dict[str, Any]) -> None:
        """Push a new server snapshot into the interpolator."""
        # TODO: SERVER INTEGRATION — This is the main snapshot handler
        self._interpolator.push_snapshot(data)

    def _on_player_eliminated(self, data: dict[str, Any]) -> None:
        """A player was eliminated."""
        eliminated_id = data.get("player_id", -1)
        if eliminated_id == self._state.local_player_id:
            self._local_alive = False

    def _on_match_end(self, data: dict[str, Any]) -> None:
        """Match has ended — transition to results screen."""
        self.app.match_results = data
        self.app.scene_manager.switch("results")

    def _on_error(self, data: dict[str, Any]) -> None:
        """Handle server errors during gameplay."""
        # Return to menu on critical errors
        self.app.scene_manager.switch("menu")

    # ----- Helpers -----

    def _find_local_snake(self) -> SnakeData | None:
        """Find the local player's snake in the current interpolated state."""
        for snake in self._state.snakes:
            if snake.id == self._state.local_player_id:
                self._local_alive = snake.alive
                self._local_score = snake.score
                return snake
        return None

    def _compute_rank(self) -> None:
        """Compute the local player's rank based on score."""
        alive_snakes = [s for s in self._state.snakes if s.alive]
        self._total_players = len(self._state.snakes)

        # Sort by score descending
        sorted_snakes = sorted(alive_snakes, key=lambda s: s.score, reverse=True)
        self._local_rank = 0
        for i, snake in enumerate(sorted_snakes):
            if snake.id == self._state.local_player_id:
                self._local_rank = i + 1
                break
        if self._local_rank == 0 and self._state.snakes:
            # Dead player — rank last
            self._local_rank = len(self._state.snakes)
