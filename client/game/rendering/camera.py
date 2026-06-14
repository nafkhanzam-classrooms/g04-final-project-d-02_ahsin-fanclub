"""
Camera — Smooth-follow camera with dead zone, lerp, and coordinate conversion.

The camera tracks the local player's snake head, providing smooth
panning with a configurable dead zone and lerp speed.
"""

from __future__ import annotations

import pygame


class Camera:
    """
    A 2D camera that follows a target position with smooth interpolation.

    Features:
        - Smooth follow via linear interpolation (lerp)
        - Configurable dead zone — the camera only moves when the target
          exits the dead zone rectangle centered on the viewport
        - World-to-screen and screen-to-world coordinate conversion

    Attributes:
        screen_width:  Viewport width in pixels.
        screen_height: Viewport height in pixels.
        lerp_speed:    Interpolation speed factor (0–1 range, per second).
        dead_zone:     Radius (pixels) of the dead zone around center.
    """

    def __init__(
        self,
        screen_width: int = 1280,
        screen_height: int = 720,
        lerp_speed: float = 5.0,
        dead_zone: float = 30.0,
    ) -> None:
        self.screen_width: int = screen_width
        self.screen_height: int = screen_height
        self.lerp_speed: float = lerp_speed
        self.dead_zone: float = dead_zone

        self._x: float = 0.0
        self._y: float = 0.0

        self._target_x: float = 0.0
        self._target_y: float = 0.0


    @property
    def position(self) -> tuple[float, float]:
        """Current camera world position (center of viewport)."""
        return (self._x, self._y)

    @property
    def target(self) -> tuple[float, float]:
        """Current target position the camera is tracking."""
        return (self._target_x, self._target_y)


    def set_target(self, x: float, y: float) -> None:
        """Set the world position the camera should follow."""
        self._target_x = x
        self._target_y = y

    def snap_to_target(self) -> None:
        """Immediately move the camera to the target (no interpolation)."""
        self._x = self._target_x
        self._y = self._target_y

    def update(self, dt: float) -> None:
        """
        Advance the camera by one frame.

        The camera only begins moving when the target exits the dead zone.
        Movement speed is smoothed by lerp.

        Args:
            dt: Delta time in seconds since the last frame.
        """
        dx = self._target_x - self._x
        dy = self._target_y - self._y

        dist_sq = dx * dx + dy * dy
        if dist_sq < self.dead_zone * self.dead_zone:
            return

        t = min(1.0, self.lerp_speed * dt)
        self._x += dx * t
        self._y += dy * t

    def world_to_screen(self, wx: float, wy: float) -> tuple[float, float]:
        """
        Convert world coordinates to screen (pixel) coordinates.

        The camera's world position maps to the center of the screen.
        """
        sx = (wx - self._x) + self.screen_width / 2.0
        sy = (wy - self._y) + self.screen_height / 2.0
        return (sx, sy)

    def screen_to_world(self, sx: float, sy: float) -> tuple[float, float]:
        """
        Convert screen (pixel) coordinates to world coordinates.
        """
        wx = (sx - self.screen_width / 2.0) + self._x
        wy = (sy - self.screen_height / 2.0) + self._y
        return (wx, wy)

    def get_visible_rect(self) -> pygame.Rect:
        """
        Return the axis-aligned bounding rectangle of the visible
        world area, useful for culling off-screen entities.
        """
        left = self._x - self.screen_width / 2.0
        top = self._y - self.screen_height / 2.0
        return pygame.Rect(int(left), int(top), self.screen_width, self.screen_height)
