"""
Lobby Scene — Shows the active room, players, and host controls.
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.ui.widgets import Button, Label
from game.networking.protocol import make_leave_room_message, make_start_room_message

if TYPE_CHECKING:
    from game.game_app import GameApp


class LobbyScene(Scene):
    """Room lobby for private rooms and hosted matches."""

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size

        self._title = Label(
            "ROOM LOBBY",
            x=sw // 2,
            y=40,
            color=(220, 230, 255),
            font_size=36,
            centered=True,
            bold=True,
        )
        self._room_code = Label("", x=sw // 2, y=90, color=(150, 190, 255), font_size=22, centered=True)
        self._host_label = Label("", x=sw // 2, y=125, color=(170, 170, 195), font_size=18, centered=True)
        self._status_label = Label("", x=sw // 2, y=155, color=(140, 140, 160), font_size=16, centered=True)

        btn_w, btn_h = 220, 50
        self._start_btn = Button(
            x=sw // 2 - btn_w - 12,
            y=sh - 90,
            width=btn_w,
            height=btn_h,
            text="START MATCH",
            on_click=self._on_start,
            font_size=20,
        )
        self._leave_btn = Button(
            x=sw // 2 + 12,
            y=sh - 90,
            width=btn_w,
            height=btn_h,
            text="LEAVE ROOM",
            on_click=self._on_leave,
            font_size=20,
        )

        self._players: list[dict[str, Any]] = []
        self._room_state: dict[str, Any] = {}
        self._status_override: str | None = None

    def enter(self) -> None:
        dispatcher = self.app.event_dispatcher
        dispatcher.subscribe("room_state", self._on_room_state)
        dispatcher.subscribe("match_found", self._on_match_found)
        dispatcher.subscribe("error", self._on_error)
        if self.app.room_state:
            self._apply_room_state(self.app.room_state)

    def exit(self) -> None:
        dispatcher = self.app.event_dispatcher
        dispatcher.unsubscribe("room_state", self._on_room_state)
        dispatcher.unsubscribe("match_found", self._on_match_found)
        dispatcher.unsubscribe("error", self._on_error)

    def handle_event(self, event: pygame.event.Event) -> None:
        self._start_btn.handle_event(event)
        self._leave_btn.handle_event(event)

    def update(self, dt: float) -> None:
        room = self._room_state
        if not room:
            return
        state = room.get("state", "waiting")
        player_count = room.get("player_count", 0)
        max_players = room.get("max_players", 0)
        default_status = f"State: {state.upper()}  Players: {player_count}/{max_players}"
        self._status_label.text = self._status_override or default_status
        current = self.app.account_state.get("account_id", -1)
        self._start_btn.rect.height = 50
        self._start_btn.rect.width = 220
        self._start_btn.rect.x = self.app.screen_size[0] // 2 - 232
        self._leave_btn.rect.x = self.app.screen_size[0] // 2 + 12
        self._start_btn.on_click = self._on_start if room.get("host_player_id") == current and room.get("can_start") else None
        self._start_btn.text = "START MATCH" if self._start_btn.on_click else "WAITING FOR HOST"

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((12, 12, 24))
        self._title.render(screen)
        self._room_code.render(screen)
        self._host_label.render(screen)
        self._status_label.render(screen)

        panel = pygame.Rect(140, 190, screen.get_width() - 280, screen.get_height() - 300)
        pygame.draw.rect(screen, (24, 26, 38), panel, border_radius=8)
        pygame.draw.rect(screen, (60, 70, 100), panel, 2, border_radius=8)

        font = pygame.font.SysFont("Arial", 20, bold=True)
        row_font = pygame.font.SysFont("Arial", 18)
        header = font.render("PLAYERS", True, (210, 220, 240))
        screen.blit(header, (panel.x + 20, panel.y + 16))

        y = panel.y + 54
        for player in self._players:
            name = str(player.get("name", "Unknown"))
            marker = "HOST  " if player.get("is_host") else ""
            row = row_font.render(f"{marker}{name}", True, (220, 220, 225))
            screen.blit(row, (panel.x + 20, y))
            y += 28

        self._start_btn.render(screen)
        self._leave_btn.render(screen)

    def _apply_room_state(self, data: dict[str, Any]) -> None:
        self._room_state = data
        self.app.room_state = data
        self._players = list(data.get("players", []))
        room_id = data.get("room_id", "unknown")
        self._room_code.text = f"Room Code: {room_id}"
        host_id = data.get("host_player_id", -1)
        host_name = "Unknown"
        for player in self._players:
            if player.get("is_host"):
                host_name = str(player.get("name", "Unknown"))
                break
        self._host_label.text = f"Host: {host_name} ({host_id})"

    def _on_room_state(self, data: dict[str, Any]) -> None:
        self._apply_room_state(data)
        self._status_override = None
        if data.get("state") == "starting":
            self.app.match_data = data
            self.app.scene_manager.switch("loading")

    def _on_match_found(self, data: dict[str, Any]) -> None:
        self.app.match_data = data
        self.app.scene_manager.switch("loading")

    def _on_error(self, data: dict[str, Any]) -> None:
        self._status_override = f"Error: {data.get('message', 'Unknown error')}"
        self._status_label.text = self._status_override

    def _on_start(self) -> None:
        if self.app.network_client.connected:
            import asyncio
            asyncio.ensure_future(self.app.network_client.send(make_start_room_message()))

    def _on_leave(self) -> None:
        if self.app.network_client.connected:
            import asyncio
            asyncio.ensure_future(self.app.network_client.send(make_leave_room_message()))
        self.app.room_state = {}
        self.app.scene_manager.switch("menu")
