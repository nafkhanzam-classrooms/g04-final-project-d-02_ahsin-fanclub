"""
Create Room Scene — Lobby for a custom room.

Displays:
    - Room code
    - Connected players
    - Kick buttons
    - Start game button
"""

from __future__ import annotations

import math
import random
import string
import time
from typing import TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.ui.widgets import (
    Button,
    Label,
    Panel,
    PlayerEntry,
    RoomCodeCard,
)

if TYPE_CHECKING:
    from game.game_app import GameApp


COLOR_BG_TOP = (10, 10, 30)
COLOR_BG_BOTTOM = (20, 15, 50)
COLOR_TITLE = (100, 220, 255)
COLOR_PARTICLE = (60, 80, 200)

class CreateRoomScene(Scene):
    """Local room lobby."""

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)

        sw, sh = app.screen_size

        self._start_time = time.monotonic()

        self._title = Label(
            "CREATE ROOM",
            x=sw // 2,
            y=70,
            color=COLOR_TITLE,
            font_size=48,
            centered=True,
            bold=True,
        )

        self._room_code_card = RoomCodeCard(
            x=sw // 2 - 180,
            y=120,
        )

        self._player_panel = Panel(
            x=sw // 2 - 300,
            y=220,
            width=600,
            height=260,
        )

        self._player_entries: list[PlayerEntry] = []

        self._start_button = Button(
            x=sw // 2 - 120,
            y=sh - 130,
            width=240,
            height=50,
            text="START GAME",
            on_click=self._on_start_game,
        )

        self._back_button = Button(
            x=sw // 2 - 120,
            y=sh - 65,
            width=240,
            height=50,
            text="BACK",
            on_click=self._on_back,
        )

        self._particles = []

        for _ in range(40):
            self._particles.append({
                "x": random.uniform(0, sw),
                "y": random.uniform(0, sh),
                "speed": random.uniform(10, 40),
                "size": random.randint(1, 3),
                "phase": random.uniform(0, math.tau),
            })

    def enter(self) -> None:
        self._room_code_card.set_room_code(
            self._generate_room_code()
        )

        self._rebuild_player_entries()

    def exit(self) -> None:
        pass

    def _generate_room_code(self) -> str:
        alphabet = (
            string.ascii_uppercase
            + string.digits
        )

        return "".join(
            random.choices(
                alphabet,
                k=6,
            )
        )
    
    def _rebuild_player_entries(self) -> None:
        usernames = [
            self.app.username,
            "Alice",
            "Bob",
        ]

        self._player_entries.clear()

        start_x = self._player_panel.rect.x + 20
        start_y = self._player_panel.rect.y + 20

        width = (
            self._player_panel.rect.width
            - 40
        )

        for i, username in enumerate(usernames):

            is_host = (i == 0)

            entry = PlayerEntry(
                x=start_x,
                y=start_y + i * 55,
                width=width,
                username=username,
                is_host=is_host,
                can_kick=not is_host,
                on_kick=(
                    lambda name=username:
                    self._kick_player(name)
                ),
            )

            self._player_entries.append(entry)

    def _kick_player(
        self,
        username: str,
    ) -> None:
        print(f"Kicked {username}")

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> None:

        self._start_button.handle_event(event)
        self._back_button.handle_event(event)

        for entry in self._player_entries:
            entry.handle_event(event)

    def update(
        self,
        dt: float,
    ) -> None:

        sw, sh = self.app.screen_size

        for p in self._particles:
            p["y"] -= p["speed"] * dt

            if p["y"] < -10:
                p["y"] = sh + 10
                p["x"] = random.uniform(0, sw)

    def render(
        self,
        screen: pygame.Surface,
    ) -> None:

        sw, sh = screen.get_size()
        elapsed = (
            time.monotonic()
            - self._start_time
        )

        for y_line in range(sh):
            ratio = y_line / sh

            r = int(
                COLOR_BG_TOP[0]
                + (
                    COLOR_BG_BOTTOM[0]
                    - COLOR_BG_TOP[0]
                )
                * ratio
            )

            g = int(
                COLOR_BG_TOP[1]
                + (
                    COLOR_BG_BOTTOM[1]
                    - COLOR_BG_TOP[1]
                )
                * ratio
            )

            b = int(
                COLOR_BG_TOP[2]
                + (
                    COLOR_BG_BOTTOM[2]
                    - COLOR_BG_TOP[2]
                )
                * ratio
            )

            pygame.draw.line(
                screen,
                (r, g, b),
                (0, y_line),
                (sw, y_line),
            )

        for p in self._particles:
            alpha = (
                0.4
                + 0.3
                * math.sin(
                    elapsed * 1.5
                    + p["phase"]
                )
            )

            c = (
                int(COLOR_PARTICLE[0] * alpha),
                int(COLOR_PARTICLE[1] * alpha),
                int(COLOR_PARTICLE[2] * alpha),
            )

            pygame.draw.circle(
                screen,
                c,
                (
                    int(p["x"]),
                    int(p["y"]),
                ),
                p["size"],
            )

        self._title.render(screen)
        self._room_code_card.render(screen)
        self._player_panel.render(screen)

        for entry in self._player_entries:
            entry.render(screen)

        self._start_button.render(screen)
        self._back_button.render(screen)


    def _on_start_game(self) -> None:
        print("Start game")
    
    def _on_back(self) -> None:
        self.app.scene_manager.switch("menu")