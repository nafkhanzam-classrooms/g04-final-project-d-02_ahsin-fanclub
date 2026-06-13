"""
Menu Scene — Main menu with Play and Quit buttons.

The first screen the player sees.  Features a title, animated
background, and two primary action buttons.
"""

from __future__ import annotations

import math
import time
from typing import TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.ui.widgets import Button, Label, TextBox

if TYPE_CHECKING:
    from game.game_app import GameApp


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

COLOR_BG_TOP = (10, 10, 30)
COLOR_BG_BOTTOM = (20, 15, 50)
COLOR_TITLE = (100, 220, 255)
COLOR_SUBTITLE = (140, 140, 180)
COLOR_PARTICLE = (60, 80, 200)


class MenuScene(Scene):
    """Main menu — Play / Quit."""

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size

        self._title = Label(
            "SNAKE.IO",
            x=sw // 2, y=sh // 4,
            color=COLOR_TITLE,
            font_size=64,
            centered=True,
            bold=True,
        )

        self._subtitle = Label(
            "Multiplayer Arena",
            x=sw // 2, y=sh // 4 + 60,
            color=COLOR_SUBTITLE,
            font_size=22,
            centered=True,
        )

        self._subtitle = Label(
            "Enter username",
            x=sw // 2, y=sh // 4 + 60,
            color=COLOR_SUBTITLE,
            font_size=22,
            centered=True,
        )

        self._username_box = TextBox(
            x=sw // 2 - 150,
            y=sh // 2 - 60,
            width=300,
            height=50,
            placeholder="Enter username",
        )

        btn_w, btn_h = 240, 55
        self._play_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 20,
            width=btn_w,
            height=btn_h,
            text="PLAY",
            on_click=self._on_play,
            font_size=26,
        )

        self._quit_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 100,
            width=btn_w,
            height=btn_h,
            text="QUIT",
            on_click=self._on_quit,
            font_size=26,
        )

        self._start_time: float = time.monotonic()

        # Decorative floating particles
        self._particles: list[dict] = []
        import random
        for _ in range(40):
            self._particles.append({
                "x": random.uniform(0, sw),
                "y": random.uniform(0, sh),
                "speed": random.uniform(10, 40),
                "size": random.randint(1, 3),
                "phase": random.uniform(0, math.tau),
            })

    # ----- Scene lifecycle -----

    def enter(self) -> None:
        """Called when entering the menu scene."""
        pass

    def exit(self) -> None:
        """Called when leaving the menu scene."""
        pass

    # ----- Event handling -----

    def handle_event(self, event: pygame.event.Event) -> None:
        self._play_btn.handle_event(event)
        self._quit_btn.handle_event(event)
        self._username_box.handle_event(event)

    # ----- Update -----

    def update(self, dt: float) -> None:
        sw, sh = self.app.screen_size
        for p in self._particles:
            p["y"] -= p["speed"] * dt
            if p["y"] < -10:
                p["y"] = sh + 10
                import random
                p["x"] = random.uniform(0, sw)

    # ----- Render -----

    def render(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        elapsed = time.monotonic() - self._start_time

        # Gradient background
        for y_line in range(sh):
            ratio = y_line / sh
            r = int(COLOR_BG_TOP[0] + (COLOR_BG_BOTTOM[0] - COLOR_BG_TOP[0]) * ratio)
            g = int(COLOR_BG_TOP[1] + (COLOR_BG_BOTTOM[1] - COLOR_BG_TOP[1]) * ratio)
            b = int(COLOR_BG_TOP[2] + (COLOR_BG_BOTTOM[2] - COLOR_BG_TOP[2]) * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y_line), (sw, y_line))

        # Floating particles
        for p in self._particles:
            alpha = 0.4 + 0.3 * math.sin(elapsed * 1.5 + p["phase"])
            c = (
                int(COLOR_PARTICLE[0] * alpha),
                int(COLOR_PARTICLE[1] * alpha),
                int(COLOR_PARTICLE[2] * alpha),
            )
            pygame.draw.circle(
                screen, c, (int(p["x"]), int(p["y"])), p["size"]
            )

        self._title.render(screen)
        self._subtitle.render(screen)
        self._play_btn.render(screen)
        self._quit_btn.render(screen)
        self._username_box.render(screen)

        # Version text
        font_tiny = pygame.font.SysFont("Arial", 12)
        ver = font_tiny.render("v0.1.0 — University Project", True, (60, 60, 80))
        screen.blit(ver, (sw // 2 - ver.get_width() // 2, sh - 30))

    # ----- Callbacks -----

    def _on_play(self) -> None:
        """Switch to matchmaking scene."""
        self.app.scene_manager.switch("matchmaking")
        username = self._username_box.get_text().strip()

        if not username:
            return

        self.app.username = username
        self.app.scene_manager.switch("matchmaking")

    def _on_quit(self) -> None:
        """Quit the game."""
        pygame.event.post(pygame.event.Event(pygame.QUIT))
