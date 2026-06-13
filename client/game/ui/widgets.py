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
