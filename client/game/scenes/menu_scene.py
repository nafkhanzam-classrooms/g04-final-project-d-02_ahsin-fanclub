"""
Menu Scene — Main menu with Play and Quit buttons.

The first screen the player sees. Features a title, animated
background, and primary action buttons.
"""

from __future__ import annotations

import math
import random
import time
from typing import TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.ui.widgets import Button, Label, TextBox
from game.scenes.join_room_modal import JoinRoomModal
from game.networking.protocol import make_join_room_message

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

        self._start_time: float = time.monotonic()
        self._error_timer: float = 0.0

        self._join_modal = JoinRoomModal(
            screen_size=app.screen_size,
            on_join=self._join_room_code,
        )

        self._title = Label(
            "SNAKE.IO",
            x=sw // 2,
            y=sh // 4,
            color=COLOR_TITLE,
            font_size=64,
            centered=True,
            bold=True,
        )

        self._subtitle = Label(
            "Multiplayer Arena",
            x=sw // 2,
            y=sh // 4 + 60,
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

        self._error_label = Label(
            "",
            x=sw // 2,
            y=self._username_box.rect.bottom + 25,
            color=(255, 100, 100),
            font_size=18,
            centered=True,
        )

        btn_w, btn_h = 240, 55

        self._create_room_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 20,
            width=btn_w,
            height=btn_h,
            text="CREATE A ROOM",
            on_click=self._on_create_room,
            font_size=26,
        )

        self._join_room_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 100,
            width=btn_w,
            height=btn_h,
            text="JOIN ROOM",
            on_click=self._on_join_room,
            font_size=26,
        )

        self._play_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 180,
            width=btn_w,
            height=btn_h,
            text="QUICKPLAY",
            on_click=self._on_play,
            font_size=26,
        )

        self._quit_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 260,
            width=btn_w,
            height=btn_h,
            text="QUIT",
            on_click=self._on_quit,
            font_size=26,
        )

        # Decorative floating particles
        self._particles: list[dict] = []
        for _ in range(40):
            self._particles.append(
                {
                    "x": random.uniform(0, sw),
                    "y": random.uniform(0, sh),
                    "speed": random.uniform(10, 40),
                    "size": random.randint(1, 3),
                    "phase": random.uniform(0, math.tau),
                }
            )

    # ----- Scene lifecycle -----

    def enter(self) -> None:
        """Called when entering the menu scene."""
        pass

    def exit(self) -> None:
        """Called when leaving the menu scene."""
        pass

    # ----- Event handling -----

    def handle_event(self, event: pygame.event.Event) -> None:
        self._username_box.handle_event(event)
        self._create_room_btn.handle_event(event)
        self._join_room_btn.handle_event(event)
        self._play_btn.handle_event(event)
        self._quit_btn.handle_event(event)
        if self._join_modal.visible:
            self._join_modal.handle_event(event)

    # ----- Update -----

    def update(self, dt: float) -> None:
        sw, sh = self.app.screen_size

        self._join_modal.update(dt)

        if self._error_timer > 0:
            self._error_timer -= dt
            if self._error_timer <= 0:
                self._error_timer = 0
                self._error_label.text = ""

        for p in self._particles:
            p["y"] -= p["speed"] * dt
            if p["y"] < -10:
                p["y"] = sh + 10
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
            pygame.draw.circle(screen, c, (int(p["x"]), int(p["y"])), p["size"])

        self._title.render(screen)
        self._subtitle.render(screen)
        self._username_box.render(screen)
        self._create_room_btn.render(screen)
        self._join_room_btn.render(screen)
        self._play_btn.render(screen)
        self._quit_btn.render(screen)
        self._join_modal.render(screen)

        if self._error_label.text:
            self._error_label.render(screen)

        # Version text
        font_tiny = pygame.font.SysFont("Arial", 12)
        ver = font_tiny.render("v0.1.0 — University Project", True, (60, 60, 80))
        screen.blit(ver, (sw // 2 - ver.get_width() // 2, sh - 30))

    # ----- Callbacks -----

    def _get_username(self) -> str:
        return self._username_box.get_text().strip()

    def _on_play(self) -> None:
        """Switch to matchmaking scene."""
        username = self._get_username()
        if not username:
            self._show_error("Username cannot be empty.")
            return

        self.app.username = username
        self.app.scene_manager.switch("matchmaking")

    def _on_create_room(self) -> None:
        """Switch to create room scene."""
        username = self._get_username()
        if not username:
            self._show_error("Username cannot be empty.")
            return

        self.app.username = username
        self.app.scene_manager.switch("create_room")

    def _on_quit(self) -> None:
        """Quit the game."""
        pygame.event.post(pygame.event.Event(pygame.QUIT))

    def _show_error(self, message: str, duration: float = 3.0) -> None:
        """Display an error message temporarily."""
        self._error_label.text = message
        self._error_timer = duration

    def _on_join_room(self) -> None:
        username = self._get_username()

        if not username:
            self._show_error("Username cannot be empty.")
            return

        self.app.username = username
        self._join_modal.open()

    def _join_room_code(self, room_code: str) -> None:
        if not self.app.username:
            self._show_error("Username cannot be empty.")
            return
        import asyncio
        async def _join() -> None:
            client = self.app.network_client
            if not client.connected and not await client.connect():
                self._show_error("Could not connect to server.")
                return
            await client.send(make_join_room_message(self.app.username, room_code))
            self.app.scene_manager.switch("lobby")
        asyncio.ensure_future(_join())
