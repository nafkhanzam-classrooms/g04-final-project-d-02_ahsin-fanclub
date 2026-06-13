"""
Reusable UI widgets for menus and screens.

Provides Button, Label, and AnimatedText primitives that can be composed
in any scene.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import Callable

import pygame


# ---------------------------------------------------------------------------
# Color constants
# ---------------------------------------------------------------------------

COLOR_BUTTON_NORMAL = (40, 44, 60)
COLOR_BUTTON_HOVER = (55, 62, 85)
COLOR_BUTTON_TEXT = (230, 230, 240)
COLOR_BUTTON_BORDER = (80, 90, 120)
COLOR_BUTTON_BORDER_HOVER = (120, 140, 200)
COLOR_LABEL_DEFAULT = (200, 200, 210)


class Button:
    """
    A styled, hoverable button with rounded corners and border glow.

    Attributes:
        rect:       Bounding rectangle (screen coordinates).
        text:       Display label.
        on_click:   Callback invoked when the button is clicked.
        font_size:  Font size in points.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        text: str,
        on_click: Callable[[], None] | None = None,
        font_size: int = 22,
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)
        self.text: str = text
        self.on_click: Callable[[], None] | None = on_click
        self.font_size: int = font_size
        self._hovered: bool = False
        self._font: pygame.font.Font = pygame.font.SysFont("Arial", font_size, bold=True)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process a Pygame event. Returns True if the button consumed it.
        """
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False

    def render(self, screen: pygame.Surface) -> None:
        """Draw the button on the given surface."""
        bg_color = COLOR_BUTTON_HOVER if self._hovered else COLOR_BUTTON_NORMAL
        border_color = (
            COLOR_BUTTON_BORDER_HOVER if self._hovered else COLOR_BUTTON_BORDER
        )

        # Background
        pygame.draw.rect(screen, bg_color, self.rect, border_radius=10)
        # Border
        pygame.draw.rect(screen, border_color, self.rect, 2, border_radius=10)

        # Text
        text_surf = self._font.render(self.text, True, COLOR_BUTTON_TEXT)
        tx = self.rect.centerx - text_surf.get_width() // 2
        ty = self.rect.centery - text_surf.get_height() // 2
        screen.blit(text_surf, (tx, ty))

    def set_position_centered(self, cx: int, cy: int) -> None:
        """Reposition the button so its center is at (cx, cy)."""
        self.rect.center = (cx, cy)


class Label:
    """
    A styled text label.

    Attributes:
        text:      Display string.
        x, y:      Screen position.
        color:     RGB text color.
        font_size: Font size.
        centered:  If True, (x, y) is the center; otherwise top-left.
    """

    def __init__(
        self,
        text: str,
        x: int = 0,
        y: int = 0,
        color: tuple[int, int, int] = COLOR_LABEL_DEFAULT,
        font_size: int = 24,
        centered: bool = False,
        bold: bool = False,
    ) -> None:
        self.text: str = text
        self.x: int = x
        self.y: int = y
        self.color: tuple[int, int, int] = color
        self.centered: bool = centered
        self._font: pygame.font.Font = pygame.font.SysFont(
            "Arial", font_size, bold=bold
        )

    def render(self, screen: pygame.Surface) -> None:
        """Draw the label."""
        surf = self._font.render(self.text, True, self.color)
        if self.centered:
            pos = (
                self.x - surf.get_width() // 2,
                self.y - surf.get_height() // 2,
            )
        else:
            pos = (self.x, self.y)
        screen.blit(surf, pos)


class AnimatedText:
    """
    A text label that animates (pulse, wave, or fade).

    Provides a subtle pulsing glow effect for loading/searching screens.
    """

    def __init__(
        self,
        text: str,
        x: int,
        y: int,
        color: tuple[int, int, int] = (200, 200, 255),
        font_size: int = 28,
        centered: bool = True,
        pulse_speed: float = 2.0,
    ) -> None:
        self.text: str = text
        self.x: int = x
        self.y: int = y
        self.base_color: tuple[int, int, int] = color
        self.centered: bool = centered
        self.pulse_speed: float = pulse_speed
        self._font: pygame.font.Font = pygame.font.SysFont(
            "Arial", font_size, bold=True
        )
        self._start_time: float = time.monotonic()

    def render(self, screen: pygame.Surface) -> None:
        """Draw the animated text with a pulsing alpha effect."""
        elapsed = time.monotonic() - self._start_time
        # Pulse between 0.4 and 1.0 brightness
        factor = 0.7 + 0.3 * math.sin(elapsed * self.pulse_speed * math.pi)

        color = (
            int(self.base_color[0] * factor),
            int(self.base_color[1] * factor),
            int(self.base_color[2] * factor),
        )

        surf = self._font.render(self.text, True, color)
        if self.centered:
            pos = (
                self.x - surf.get_width() // 2,
                self.y - surf.get_height() // 2,
            )
        else:
            pos = (self.x, self.y)
        screen.blit(surf, pos)

    def update_text(self, new_text: str) -> None:
        """Change the displayed text."""
        self.text = new_text


class LoadingDots:
    """
    Animated loading indicator with bouncing dots.
    """

    def __init__(
        self,
        x: int,
        y: int,
        color: tuple[int, int, int] = (150, 160, 255),
        dot_count: int = 5,
        dot_radius: int = 6,
        spacing: int = 20,
    ) -> None:
        self.x: int = x
        self.y: int = y
        self.color: tuple[int, int, int] = color
        self.dot_count: int = dot_count
        self.dot_radius: int = dot_radius
        self.spacing: int = spacing
        self._start_time: float = time.monotonic()

    def render(self, screen: pygame.Surface) -> None:
        """Draw the bouncing dots animation."""
        elapsed = time.monotonic() - self._start_time
        total_width = (self.dot_count - 1) * self.spacing
        start_x = self.x - total_width // 2

        for i in range(self.dot_count):
            # Each dot bounces with a phase offset
            phase = elapsed * 3.0 - i * 0.4
            bounce = abs(math.sin(phase)) * 12.0

            dx = start_x + i * self.spacing
            dy = self.y - bounce

            # Brightness varies with bounce
            factor = 0.5 + 0.5 * abs(math.sin(phase))
            c = (
                int(self.color[0] * factor),
                int(self.color[1] * factor),
                int(self.color[2] * factor),
            )

            pygame.draw.circle(screen, c, (int(dx), int(dy)), self.dot_radius)

class TextBox:
    """
    A styled single-line text input widget.

    Supports:
        - Mouse focus
        - Keyboard input
        - Placeholder text
        - Blinking cursor
        - Maximum length
        - Optional Enter callback
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        placeholder: str = "",
        font_size: int = 22,
        max_length: int = 16,
        on_enter: Callable[[str], None] | None = None,
    ) -> None:
        self.rect: pygame.Rect = pygame.Rect(x, y, width, height)

        self.text: str = ""
        self.placeholder: str = placeholder
        self.max_length: int = max_length
        self.on_enter = on_enter

        self.active: bool = False
        self._hovered: bool = False

        self._font: pygame.font.Font = pygame.font.SysFont(
            "Arial",
            font_size,
        )

        self._cursor_visible: bool = True
        self._cursor_timer: float = time.monotonic()

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Process a Pygame event.

        Returns:
            True if the textbox consumed the event.
        """

        if event.type == pygame.MOUSEMOTION:
            self._hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.active = self.rect.collidepoint(event.pos)
            return self.active

        elif event.type == pygame.KEYDOWN and self.active:

            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True

            elif event.key == pygame.K_RETURN:
                if self.on_enter:
                    self.on_enter(self.text)
                return True

            else:
                if (
                    len(self.text) < self.max_length
                    and (
                        event.unicode.isalnum()
                        or event.unicode == "_"
                    )
                ):
                    self.text += event.unicode
                    return True

        return False

    def render(self, screen: pygame.Surface) -> None:
        """Draw the textbox."""

        bg_color = (
            COLOR_BUTTON_HOVER
            if self.active or self._hovered
            else COLOR_BUTTON_NORMAL
        )

        border_color = (
            COLOR_BUTTON_BORDER_HOVER
            if self.active
            else COLOR_BUTTON_BORDER
        )

        pygame.draw.rect(
            screen,
            bg_color,
            self.rect,
            border_radius=10,
        )

        pygame.draw.rect(
            screen,
            border_color,
            self.rect,
            2,
            border_radius=10,
        )

        # Placeholder
        if self.text:
            display_text = self.text
            text_color = COLOR_BUTTON_TEXT
        else:
            display_text = self.placeholder
            text_color = (120, 120, 140)

        text_surf = self._font.render(
            display_text,
            True,
            text_color,
        )

        tx = self.rect.x + 12
        ty = self.rect.centery - text_surf.get_height() // 2

        screen.blit(text_surf, (tx, ty))

        # Blinking cursor
        if self.active and self.text:
            elapsed = time.monotonic()

            if elapsed - self._cursor_timer >= 0.5:
                self._cursor_visible = (
                    not self._cursor_visible
                )
                self._cursor_timer = elapsed

            if self._cursor_visible:
                cursor_x = tx + text_surf.get_width() + 2
                cursor_y1 = ty
                cursor_y2 = ty + text_surf.get_height()

                pygame.draw.line(
                    screen,
                    COLOR_BUTTON_TEXT,
                    (cursor_x, cursor_y1),
                    (cursor_x, cursor_y2),
                    2,
                )

    def get_text(self) -> str:
        """Return the current text."""
        return self.text

    def set_text(self, text: str) -> None:
        """Set the textbox content."""
        self.text = text[: self.max_length]

    def clear(self) -> None:
        """Clear the textbox."""
        self.text = ""

class Panel:
    """
    Reusable rounded rectangular panel.

    Used for:
        - Room code containers
        - Player lists
        - Dialog boxes
        - Scoreboards
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        background: tuple[int, int, int] = (30, 35, 50),
        border: tuple[int, int, int] = (80, 90, 120),
        border_radius: int = 10,
        border_width: int = 2,
    ) -> None:
        self.rect = pygame.Rect(
            x,
            y,
            width,
            height,
        )

        self.background = background
        self.border = border
        self.border_radius = border_radius
        self.border_width = border_width

    def render(self, screen: pygame.Surface) -> None:
        pygame.draw.rect(
            screen,
            self.background,
            self.rect,
            border_radius=self.border_radius,
        )

        pygame.draw.rect(
            screen,
            self.border,
            self.rect,
            self.border_width,
            border_radius=self.border_radius,
        )

class RoomCodeCard:
    """
    Displays the room code inside a styled panel.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int = 360,
        height: int = 60,
        room_code: str = "",
    ) -> None:
        self.panel = Panel(
            x,
            y,
            width,
            height,
        )

        self.room_code = room_code

        self._font = pygame.font.SysFont(
            "Arial",
            28,
            bold=True,
        )

    def set_room_code(self, room_code: str) -> None:
        self.room_code = room_code

    def render(
        self,
        screen: pygame.Surface,
    ) -> None:
        self.panel.render(screen)

        text = self._font.render(
            f"Room Code: {self.room_code}",
            True,
            (220, 220, 230),
        )

        screen.blit(
            text,
            (
                self.panel.rect.centerx
                - text.get_width() // 2,
                self.panel.rect.centery
                - text.get_height() // 2,
            ),
        )

class PlayerEntry:
    """
    Represents one player row inside the lobby.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        username: str,
        is_host: bool = False,
        can_kick: bool = False,
        on_kick: Callable[[], None] | None = None,
    ) -> None:
        self.rect = pygame.Rect(
            x,
            y,
            width,
            45,
        )

        self.username = username
        self.is_host = is_host
        self.can_kick = can_kick

        self._font = pygame.font.SysFont(
            "Arial",
            22,
        )

        self._kick_button = None

        if can_kick:
            self._kick_button = Button(
                x=self.rect.right - 90,
                y=self.rect.y + 5,
                width=80,
                height=35,
                text="KICK",
                on_click=on_kick,
                font_size=18,
            )
            
    def handle_event(
        self,
        event: pygame.event.Event,
    ) -> bool:
        if self._kick_button:
            return self._kick_button.handle_event(event)

        return False
    
    def render(
        self,
        screen: pygame.Surface,
    ) -> None:

        pygame.draw.rect(
            screen,
            (40, 44, 60),
            self.rect,
            border_radius=8,
        )

        text = self.username

        if self.is_host:
            text += " (Host)"

        surf = self._font.render(
            text,
            True,
            (220, 220, 230),
        )

        screen.blit(
            surf,
            (
                self.rect.x + 15,
                self.rect.centery
                - surf.get_height() // 2,
            ),
        )

        if self._kick_button:
            self._kick_button.render(screen)