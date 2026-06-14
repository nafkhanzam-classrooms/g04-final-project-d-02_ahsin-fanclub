"""
Loading Scene — Displayed after a match is found, before gameplay starts.

Shows match found confirmation, player count, and a loading progress bar.
Transitions to GameplayScene when the server sends MATCH_START.
"""

from __future__ import annotations

import math
import time
from typing import Any, TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.ui.widgets import AnimatedText, Label

if TYPE_CHECKING:
    from game.game_app import GameApp


class LoadingScene(Scene):
    """Loading screen — match found, player count, countdown."""

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size

        self._match_found_text = AnimatedText(
            "Match Found!",
            x=sw // 2,
            y=sh // 3,
            color=(80, 255, 160),
            font_size=42,
            pulse_speed=1.5,
        )

        self._player_count_label = Label(
            "Players: ...",
            x=sw // 2,
            y=sh // 3 + 70,
            color=(180, 180, 200),
            font_size=22,
            centered=True,
        )

        self._loading_label = Label(
            "Preparing arena...",
            x=sw // 2,
            y=sh // 2 + 60,
            color=(120, 120, 150),
            font_size=18,
            centered=True,
        )

        self._progress: float = 0.0
        self._start_time: float = time.monotonic()
        self._player_count: int = 0

    # ----- Lifecycle -----

    def enter(self) -> None:
        """Subscribe to MATCH_START and extract match data."""
        self.app.event_dispatcher.subscribe("match_start", self._on_match_start)
        self.app.event_dispatcher.subscribe("error", self._on_error)

        # Extract player count from match_found data
        match_data = getattr(self.app, "match_data", {})
        self._player_count = match_data.get("player_count", 0)
        self._player_count_label.text = f"Players: {self._player_count}"

    def exit(self) -> None:
        self.app.event_dispatcher.unsubscribe("match_start", self._on_match_start)
        self.app.event_dispatcher.unsubscribe("error", self._on_error)

    # ----- Events -----

    def handle_event(self, event: pygame.event.Event) -> None:
        pass  # No interactive elements

    def update(self, dt: float) -> None:
        # MATCH_START_COUNTDOWN of 3.0 seconds. Previously used dt * 0.5
        # which filled in ~2s (visual mismatch with 3.0s countdown).
        # 1.0 / 3.0 ≈ 0.333 fills the bar in exactly 3.0 seconds.
        self._progress = min(1.0, self._progress + dt * (1.0 / 3.0))

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((10, 10, 24))
        sw, sh = screen.get_size()

        self._match_found_text.render(screen)
        self._player_count_label.render(screen)
        self._loading_label.render(screen)

        # Progress bar
        bar_w = 300
        bar_h = 12
        bar_x = sw // 2 - bar_w // 2
        bar_y = sh // 2 + 20

        # Background
        pygame.draw.rect(
            screen, (30, 30, 50),
            (bar_x, bar_y, bar_w, bar_h),
            border_radius=6,
        )

        # Fill
        fill_w = int(bar_w * self._progress)
        if fill_w > 0:
            # Gradient-ish fill
            fill_color = (
                int(60 + 140 * self._progress),
                int(180 + 60 * self._progress),
                255,
            )
            pygame.draw.rect(
                screen, fill_color,
                (bar_x, bar_y, fill_w, bar_h),
                border_radius=6,
            )

        # Border
        pygame.draw.rect(
            screen, (80, 90, 120),
            (bar_x, bar_y, bar_w, bar_h),
            1, border_radius=6,
        )

        # Spinning icon
        elapsed = time.monotonic() - self._start_time
        cx, cy = sw // 2, sh // 2 + 120
        for i in range(8):
            angle = elapsed * 3.0 + i * (math.tau / 8)
            r = 20
            dx = cx + math.cos(angle) * r
            dy = cy + math.sin(angle) * r
            alpha = (i + 1) / 8
            c = (int(100 * alpha), int(150 * alpha), int(255 * alpha))
            pygame.draw.circle(screen, c, (int(dx), int(dy)), 3)

    # ----- Server events -----

    def _on_match_start(self, data: dict[str, Any]) -> None:
        """Server signals match start — switch to gameplay."""
        # TODO: SERVER INTEGRATION — Extract any initial state from data
        self.app.scene_manager.switch("gameplay")

    def _on_error(self, data: dict[str, Any]) -> None:
        """Handle errors — return to menu."""
        self.app.scene_manager.switch("menu")
