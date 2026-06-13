"""
Renderer — Draws the game world: background grid, arena boundary,
snakes, food, and visual effects.

All drawing uses the Camera for world-to-screen coordinate conversion.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import pygame

from game.entities.food import FoodData
from game.entities.snake import SnakeData
from game.rendering.camera import Camera

if TYPE_CHECKING:
    from game.rendering.interpolation import InterpolatedState


# ---------------------------------------------------------------------------
# Color palette
# ---------------------------------------------------------------------------

COLOR_BG = (15, 15, 25)
COLOR_GRID = (25, 25, 40)
COLOR_ARENA_BORDER = (255, 60, 80)
COLOR_ARENA_FILL = (12, 12, 20)

# Snake color palette — each snake gets a different color based on ID
SNAKE_COLORS: list[tuple[int, int, int]] = [
    (0, 230, 118),    # Green
    (41, 121, 255),   # Blue
    (255, 196, 0),    # Amber
    (213, 0, 249),    # Purple
    (255, 61, 0),     # Deep Orange
    (0, 229, 255),    # Cyan
    (255, 110, 64),   # Coral
    (118, 255, 3),    # Lime
]

FOOD_COLORS: list[tuple[int, int, int]] = [
    (255, 82, 82),
    (255, 167, 38),
    (102, 187, 106),
    (66, 165, 245),
    (171, 71, 188),
    (255, 238, 88),
]


# ---------------------------------------------------------------------------
# Arena configuration
# ---------------------------------------------------------------------------

ARENA_WIDTH: int = 2000
ARENA_HEIGHT: int = 2000
GRID_SPACING: int = 50


class Renderer:
    """
    Draws the game world onto a Pygame surface.

    Uses the Camera for all coordinate conversions, so entities
    are drawn relative to the viewport.
    """

    def __init__(self, camera: Camera) -> None:
        self._camera: Camera = camera

    @property
    def camera(self) -> Camera:
        return self._camera

    # ----- Public API -----

    def render_frame(
        self,
        screen: pygame.Surface,
        state: "InterpolatedState",
    ) -> None:
        """Draw one complete frame of the game world."""
        screen.fill(COLOR_BG)
        self._render_grid(screen)
        self._render_arena_boundary(screen)
        self._render_foods(screen, state.foods)
        self._render_snakes(screen, state.snakes, state.local_player_id)

    # ----- Background grid -----

    def _render_grid(self, screen: pygame.Surface) -> None:
        """Draw a subtle grid pattern for spatial awareness."""
        vis = self._camera.get_visible_rect()
        sw, sh = screen.get_size()

        # Compute grid-aligned start positions
        start_x = vis.left - (vis.left % GRID_SPACING)
        start_y = vis.top - (vis.top % GRID_SPACING)

        for gx in range(start_x, vis.right + GRID_SPACING, GRID_SPACING):
            sx, _ = self._camera.world_to_screen(gx, 0)
            pygame.draw.line(screen, COLOR_GRID, (sx, 0), (sx, sh), 1)

        for gy in range(start_y, vis.bottom + GRID_SPACING, GRID_SPACING):
            _, sy = self._camera.world_to_screen(0, gy)
            pygame.draw.line(screen, COLOR_GRID, (0, sy), (sw, sy), 1)

    # ----- Arena boundary -----

    def _render_arena_boundary(self, screen: pygame.Surface) -> None:
        """Draw the arena boundary rectangle."""
        # Top-left and bottom-right in screen coords
        sx1, sy1 = self._camera.world_to_screen(0, 0)
        sx2, sy2 = self._camera.world_to_screen(ARENA_WIDTH, ARENA_HEIGHT)

        rect = pygame.Rect(
            int(sx1), int(sy1),
            int(sx2 - sx1), int(sy2 - sy1),
        )

        # Dim area outside the arena
        # (skip for performance — only draw the border line)
        pygame.draw.rect(screen, COLOR_ARENA_BORDER, rect, 3)

    # ----- Snakes -----

    def _render_snakes(
        self,
        screen: pygame.Surface,
        snakes: list[SnakeData],
        local_id: int,
    ) -> None:
        """Draw all snakes. The local player's snake is drawn last (on top)."""
        # Sort: local snake drawn last
        sorted_snakes = sorted(snakes, key=lambda s: s.id == local_id)

        for snake in sorted_snakes:
            if not snake.alive:
                continue
            self._draw_snake(screen, snake, is_local=(snake.id == local_id))

    def _draw_snake(
        self,
        screen: pygame.Surface,
        snake: SnakeData,
        is_local: bool,
    ) -> None:
        """Draw a single snake with a glowing head and tapered body."""
        color = SNAKE_COLORS[snake.id % len(SNAKE_COLORS)]

        if not snake.segments:
            return

        segment_count = len(snake.segments)

        # Draw body segments (back to front)
        for i in reversed(range(segment_count)):
            seg = snake.segments[i]
            sx, sy = self._camera.world_to_screen(seg.x, seg.y)

            # Taper: head is largest, tail is smallest
            progress = 1.0 - (i / max(segment_count, 1))
            radius = max(3, int(10 * (0.4 + 0.6 * progress)))

            # Darken body segments slightly
            body_color = (
                max(0, color[0] - int(40 * (1.0 - progress))),
                max(0, color[1] - int(40 * (1.0 - progress))),
                max(0, color[2] - int(40 * (1.0 - progress))),
            )

            pygame.draw.circle(screen, body_color, (int(sx), int(sy)), radius)

            # Outline
            outline_color = (
                min(255, body_color[0] + 30),
                min(255, body_color[1] + 30),
                min(255, body_color[2] + 30),
            )
            pygame.draw.circle(
                screen, outline_color, (int(sx), int(sy)), radius, 2
            )

        # Draw head with glow effect
        head = snake.segments[0]
        hx, hy = self._camera.world_to_screen(head.x, head.y)

        # Glow
        glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        glow_color = (*color, 60)
        pygame.draw.circle(glow_surf, glow_color, (20, 20), 18)
        screen.blit(
            glow_surf,
            (int(hx) - 20, int(hy) - 20),
            special_flags=pygame.BLEND_RGBA_ADD,
        )

        # Head circle
        pygame.draw.circle(screen, color, (int(hx), int(hy)), 12)

        # Eyes
        angle_rad = math.radians(snake.direction)
        eye_offset = 5
        for sign in (-1, 1):
            perp_angle = angle_rad + sign * math.pi / 2
            ex = hx + math.cos(perp_angle) * eye_offset
            ey = hy + math.sin(perp_angle) * eye_offset
            pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), 3)
            # Pupil
            px = ex + math.cos(angle_rad) * 1.5
            py = ey + math.sin(angle_rad) * 1.5
            pygame.draw.circle(screen, (10, 10, 10), (int(px), int(py)), 1)

        # Draw name label above the head
        if snake.name:
            font = pygame.font.SysFont("Arial", 14, bold=True)
            name_surf = font.render(snake.name, True, (220, 220, 220))
            screen.blit(
                name_surf,
                (int(hx) - name_surf.get_width() // 2, int(hy) - 28),
            )

    # ----- Food -----

    def _render_foods(
        self, screen: pygame.Surface, foods: list[FoodData]
    ) -> None:
        """Draw all food items as small glowing dots."""
        vis = self._camera.get_visible_rect()

        for i, food in enumerate(foods):
            # Frustum culling — skip off-screen food
            if not vis.collidepoint(int(food.x), int(food.y)):
                continue

            sx, sy = self._camera.world_to_screen(food.x, food.y)
            color = FOOD_COLORS[i % len(FOOD_COLORS)]

            # Outer glow
            glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            glow_color = (*color, 50)
            pygame.draw.circle(glow_surf, glow_color, (10, 10), 8)
            screen.blit(
                glow_surf,
                (int(sx) - 10, int(sy) - 10),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

            # Core
            pygame.draw.circle(screen, color, (int(sx), int(sy)), 4)
