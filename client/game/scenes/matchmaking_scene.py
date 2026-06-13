"""
Matchmaking Scene — Searching for a match with animation.

Displays a searching animation, queue status, and a Cancel button.
Connects to the server and sends a JOIN_QUEUE request.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.networking.protocol import make_join_queue_message, make_cancel_queue_message
from game.ui.widgets import AnimatedText, Button, Label, LoadingDots

if TYPE_CHECKING:
    from game.game_app import GameApp


class MatchmakingScene(Scene):
    """Matchmaking screen — searching animation, queue status, cancel."""

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size

        self._searching_text = AnimatedText(
            "Searching for a match...",
            x=sw // 2,
            y=sh // 2 - 40,
            color=(150, 180, 255),
            font_size=30,
            pulse_speed=2.0,
        )

        self._dots = LoadingDots(
            x=sw // 2,
            y=sh // 2 + 30,
            color=(120, 140, 255),
        )

        self._status_label = Label(
            "Connecting to server...",
            x=sw // 2,
            y=sh // 2 + 80,
            color=(100, 100, 130),
            font_size=16,
            centered=True,
        )

        btn_w, btn_h = 200, 50
        self._cancel_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh // 2 + 140,
            width=btn_w,
            height=btn_h,
            text="CANCEL",
            on_click=self._on_cancel,
            font_size=20,
        )

        self._queue_position: int = 0
        self._players_in_queue: int = 0
        self._start_time: float = time.monotonic()

    # ----- Scene lifecycle -----

    def enter(self) -> None:
        """Connect to server and request matchmaking."""
        # Subscribe to server events
        dispatcher = self.app.event_dispatcher
        dispatcher.subscribe("match_found", self._on_match_found)
        dispatcher.subscribe("queue_status", self._on_queue_status)
        dispatcher.subscribe("error", self._on_error)

        # TODO: SERVER INTEGRATION — Connect to server and send join_queue
        asyncio.ensure_future(self._connect_and_queue())

    def exit(self) -> None:
        """Unsubscribe from events."""
        dispatcher = self.app.event_dispatcher
        dispatcher.unsubscribe("match_found", self._on_match_found)
        dispatcher.unsubscribe("queue_status", self._on_queue_status)
        dispatcher.unsubscribe("error", self._on_error)

    # ----- Event handling -----

    def handle_event(self, event: pygame.event.Event) -> None:
        self._cancel_btn.handle_event(event)

    def update(self, dt: float) -> None:
        elapsed = time.monotonic() - self._start_time
        elapsed_int = int(elapsed)
        self._status_label.text = (
            f"In queue — {elapsed_int}s elapsed"
            if self.app.network_client.connected
            else "Connecting to server..."
        )

    def render(self, screen: pygame.Surface) -> None:
        screen.fill((12, 12, 28))

        self._searching_text.render(screen)
        self._dots.render(screen)
        self._status_label.render(screen)
        self._cancel_btn.render(screen)

    # ----- Network -----

    async def _connect_and_queue(self) -> None:
        """Connect to the WebSocket server and join the matchmaking queue."""
        client = self.app.network_client
        if not client.connected:
            success = await client.connect()
            if not success:
                self._status_label.text = "Connection failed — retrying..."
                return

        # TODO: SERVER INTEGRATION — Send join_queue message
        await client.send(make_join_queue_message())

    # ----- Event handlers -----

    def _on_match_found(self, data: dict[str, Any]) -> None:
        """Server found a match — transition to loading scene."""
        self.app.match_data = data
        self.app.scene_manager.switch("loading")

    def _on_queue_status(self, data: dict[str, Any]) -> None:
        """Update queue position display."""
        self._queue_position = data.get("position", 0)
        self._players_in_queue = data.get("players_in_queue", 0)

    def _on_error(self, data: dict[str, Any]) -> None:
        """Handle server errors during matchmaking."""
        msg = data.get("message", "Unknown error")
        self._status_label.text = f"Error: {msg}"

    def _on_cancel(self) -> None:
        """Cancel matchmaking and return to menu."""
        if self.app.network_client.connected:
            asyncio.ensure_future(
                self.app.network_client.send(make_cancel_queue_message())
            )
        self.app.scene_manager.switch("menu")
