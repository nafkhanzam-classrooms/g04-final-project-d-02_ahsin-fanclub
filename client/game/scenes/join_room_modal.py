"""
Join Room modal popup.

Displays:
    - Title
    - Room code textbox
    - JOIN button

This component is intended to be embedded inside MenuScene.
"""

from __future__ import annotations

from typing import Callable

import pygame

from game.ui.widgets import (
    Button,
    Label,
    Panel,
    TextBox,
)


class JoinRoomModal:
    """
    Modal popup for entering a room code.

    Usage:
        self._join_modal = JoinRoomModal(
            screen_size=app.screen_size,
            on_join=self._on_join_room_code,
        )
    """

    def __init__(
        self,
        screen_size: tuple[int, int],
        on_join: Callable[[str], None] | None = None,
    ) -> None:
        sw, sh = screen_size

        self.visible: bool = False
        self._on_join = on_join

        modal_w = 420
        modal_h = 260

        x = sw // 2 - modal_w // 2
        y = sh // 2 - modal_h // 2

        self._panel = Panel(
            x=x,
            y=y,
            width=modal_w,
            height=modal_h,
        )

        self._title = Label(
            "JOIN ROOM",
            x=sw // 2,
            y=y + 45,
            font_size=30,
            centered=True,
            bold=True,
        )

        self._code_box = TextBox(
            x=x + 60,
            y=y + 95,
            width=modal_w - 120,
            height=50,
            placeholder="Enter room code",
            max_length=6,
            on_enter=self._submit,
        )

        btn_w = 180
        btn_h = 50

        self._join_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=y + 175,
            width=btn_w,
            height=btn_h,
            text="JOIN",
            on_click=self._submit,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open(self) -> None:
        """Open the modal."""
        self.visible = True
        self._code_box.active = True

    def close(self) -> None:
        """Close the modal and clear input."""
        self.visible = False
        self._code_box.clear()
        self._code_box.active = False

    def get_room_code(self) -> str:
        """Return the current room code."""
        return self._code_box.get_text().strip()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _submit(
        self,
        text: str | None = None,
    ) -> None:
        """
        Triggered when JOIN is pressed or Enter is hit.
        """

        room_code = self.get_room_code()

        if not room_code:
            return

        if self._on_join:
            self._on_join(room_code)

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------

    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> bool:
        """
        Returns True if the modal consumed the event.
        """

        if not self.visible:
            return False

        if self._code_box.handle_event(event):
            return True

        if self._join_btn.handle_event(event):
            return True

        return True

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        dt: float,
    ) -> None:
        """
        Reserved for future animations.
        """
        pass

    # ------------------------------------------------------------------
    # Render
    # ------------------------------------------------------------------

    def render(
        self,
        screen: pygame.Surface,
    ) -> None:
        if not self.visible:
            return

        # Dark overlay
        overlay = pygame.Surface(
            screen.get_size(),
            pygame.SRCALPHA,
        )
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        self._panel.render(screen)
        self._title.render(screen)
        self._code_box.render(screen)
        self._join_btn.render(screen)
