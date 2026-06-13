"""
Create Room Scene — server-backed host lobby for a new room.
"""

from __future__ import annotations

import asyncio
import math
import random
import time
from typing import TYPE_CHECKING, Any

import pygame

from game.networking.protocol import make_create_room_message, make_leave_room_message, make_start_room_message
from game.scene_manager import Scene
from game.ui.widgets import Button, Label, Panel, PlayerEntry, RoomCodeCard

if TYPE_CHECKING:
    from game.game_app import GameApp


class CreateRoomScene(Scene):
    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size
        self._start_time = time.monotonic()
        self._room_state: dict[str, Any] = {}
        self._status_text = "Creating room..."
        self._title = Label("CREATE ROOM", x=sw // 2, y=70, color=(100, 220, 255), font_size=48, centered=True, bold=True)
        self._room_code_card = RoomCodeCard(x=sw // 2 - 180, y=120)
        self._player_panel = Panel(x=sw // 2 - 300, y=220, width=600, height=260)
        self._status_label = Label(self._status_text, x=sw // 2, y=190, color=(180, 180, 210), font_size=16, centered=True)
        self._player_entries: list[PlayerEntry] = []
        self._start_button = Button(x=sw // 2 - 120, y=sh - 130, width=240, height=50, text="START GAME", on_click=self._on_start_game)
        self._back_button = Button(x=sw // 2 - 120, y=sh - 65, width=240, height=50, text="BACK", on_click=self._on_back)
        self._particles: list[dict[str, float | int]] = []
        for _ in range(40):
            self._particles.append({
                "x": random.uniform(0, sw),
                "y": random.uniform(0, sh),
                "speed": random.uniform(10, 40),
                "size": random.randint(1, 3),
                "phase": random.uniform(0, math.tau),
            })

    def enter(self) -> None:
        d = self.app.event_dispatcher
        d.subscribe("room_state", self._on_room_state)
        d.subscribe("error", self._on_error)
        self._apply_room_state({})
        asyncio.ensure_future(self._connect_and_create_room())

    def exit(self) -> None:
        d = self.app.event_dispatcher
        d.unsubscribe("room_state", self._on_room_state)
        d.unsubscribe("error", self._on_error)

    def handle_event(self, event: pygame.event.Event) -> None:
        self._start_button.handle_event(event)
        self._back_button.handle_event(event)
        for entry in self._player_entries:
            entry.handle_event(event)

    def update(self, dt: float) -> None:
        sw, sh = self.app.screen_size
        for p in self._particles:
            p["y"] -= float(p["speed"]) * dt
            if p["y"] < -10:
                p["y"] = sh + 10
                p["x"] = random.uniform(0, sw)
        self._status_label.text = self._status_text
        room = self._room_state
        if room:
            current = room.get("local_player_id", -1)
            is_host = room.get("host_player_id") == current
            self._start_button.on_click = self._on_start_game if is_host and room.get("can_start") else None
            self._start_button.text = "START GAME" if self._start_button.on_click else "WAITING FOR HOST"

    def render(self, screen: pygame.Surface) -> None:
        sw, sh = screen.get_size()
        elapsed = time.monotonic() - self._start_time
        top, bottom = (10, 10, 30), (20, 15, 50)
        for y in range(sh):
            ratio = y / sh
            color = tuple(int(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
            pygame.draw.line(screen, color, (0, y), (sw, y))
        for p in self._particles:
            alpha = 0.4 + 0.3 * math.sin(elapsed * 1.5 + float(p["phase"]))
            c = tuple(int(v * alpha) for v in (60, 80, 200))
            pygame.draw.circle(screen, c, (int(p["x"]), int(p["y"])), int(p["size"]))
        self._title.render(screen)
        self._room_code_card.render(screen)
        self._status_label.render(screen)
        self._player_panel.render(screen)
        for entry in self._player_entries:
            entry.render(screen)
        self._start_button.render(screen)
        self._back_button.render(screen)

    async def _connect_and_create_room(self) -> None:
        client = self.app.network_client
        if not client.connected and not await client.connect():
            self._status_text = "Connection failed."
            return
        await client.send(make_create_room_message(self.app.username))

    def _apply_room_state(self, data: dict[str, Any]) -> None:
        self._room_state = data
        self.app.room_state = data
        if not data:
            self._room_code_card.set_room_code("PENDING")
            self._status_text = "Creating room..."
            self._player_entries = self._make_entries([self.app.username])
            return
        self._room_code_card.set_room_code(str(data.get("room_id", "UNKNOWN")))
        self._status_text = f"Room {data.get('room_id', 'UNKNOWN')} ready"
        self._player_entries = self._make_entries([str(p.get("name", "Unknown")) for p in data.get("players", [])])

    def _make_entries(self, usernames: list[str]) -> list[PlayerEntry]:
        entries: list[PlayerEntry] = []
        start_x = self._player_panel.rect.x + 20
        start_y = self._player_panel.rect.y + 20
        width = self._player_panel.rect.width - 40
        for i, username in enumerate(usernames):
            is_host = i == 0
            entries.append(PlayerEntry(
                x=start_x,
                y=start_y + i * 55,
                width=width,
                username=username,
                is_host=is_host,
                can_kick=not is_host,
                on_kick=lambda name=username: self._kick_player(name),
            ))
        return entries

    def _kick_player(self, username: str) -> None:
        self._status_text = f"Kick not implemented for {username}"

    def _on_room_state(self, data: dict[str, Any]) -> None:
        self._apply_room_state(data)
        if data.get("state") == "starting":
            self.app.match_data = data
            self.app.scene_manager.switch("loading")

    def _on_error(self, data: dict[str, Any]) -> None:
        self._status_text = f"Error: {data.get('message', 'Unknown error')}"

    def _on_start_game(self) -> None:
        if self.app.network_client.connected:
            asyncio.ensure_future(self.app.network_client.send(make_start_room_message()))

    def _on_back(self) -> None:
        if self.app.network_client.connected:
            asyncio.ensure_future(self.app.network_client.send(make_leave_room_message()))
        self.app.room_state = {}
        self.app.scene_manager.switch("menu")
