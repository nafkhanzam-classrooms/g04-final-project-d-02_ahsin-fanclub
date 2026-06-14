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



COLOR_BG = (15, 15, 25)
COLOR_GRID = (25, 25, 40)
COLOR_ARENA_BORDER = (255, 60, 80)
COLOR_ARENA_FILL = (12, 12, 20)

SNAKE_COLORS: list[tuple[int, int, int]] = [
    (0, 230, 118),
    (41, 121, 255),
    (255, 196, 0),
    (213, 0, 249),
    (255, 61, 0),
    (0, 229, 255),
    (255, 110, 64),
    (118, 255, 3),
]

FOOD_COLORS: list[tuple[int, int, int]] = [
    (255, 82, 82),
    (255, 167, 38),
    (102, 187, 106),
    (66, 165, 245),
    (171, 71, 188),
    (255, 238, 88),
]



ARENA_WIDTH: int = 4000
ARENA_HEIGHT: int = 4000
GRID_SPACING: int = 50


class Renderer:
    """
    Draws the game world onto a Pygame surface.

    Uses the Camera for all coordinate conversions, so entities
    are drawn relative to the viewport.
    """

    def __init__(self, camera: Camera) -> None:
        self._camera: Camera = camera
        self._name_font: pygame.font.Font = pygame.font.SysFont("Arial", 14, bold=True)

    @property
    def camera(self) -> Camera:
        return self._camera


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


    def _render_grid(self, screen: pygame.Surface) -> None:
        """Draw a subtle grid pattern for spatial awareness."""
        vis = self._camera.get_visible_rect()
        sw, sh = screen.get_size()

        start_x = vis.left - (vis.left % GRID_SPACING)
        start_y = vis.top - (vis.top % GRID_SPACING)

        for gx in range(start_x, vis.right + GRID_SPACING, GRID_SPACING):
            sx, _ = self._camera.world_to_screen(gx, 0)
            pygame.draw.line(screen, COLOR_GRID, (sx, 0), (sx, sh), 1)

        for gy in range(start_y, vis.bottom + GRID_SPACING, GRID_SPACING):
            _, sy = self._camera.world_to_screen(0, gy)
            pygame.draw.line(screen, COLOR_GRID, (0, sy), (sw, sy), 1)


    def _render_arena_boundary(self, screen: pygame.Surface) -> None:
        """Draw the arena boundary rectangle."""
        sx1, sy1 = self._camera.world_to_screen(0, 0)
        sx2, sy2 = self._camera.world_to_screen(ARENA_WIDTH, ARENA_HEIGHT)

        rect = pygame.Rect(
            int(sx1), int(sy1),
            int(sx2 - sx1), int(sy2 - sy1),
        )

        pygame.draw.rect(screen, COLOR_ARENA_BORDER, rect, 3)


    def _render_snakes(
        self,
        screen: pygame.Surface,
        snakes: list[SnakeData],
        local_id: int,
    ) -> None:
        """Draw all snakes. The local player's snake is drawn last (on top)."""
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
        """Draw a single snake with a uniform body and distinct head."""
        color = SNAKE_COLORS[snake.id % len(SNAKE_COLORS)]

        if not snake.segments:
            return

        segment_count = len(snake.segments)
        size_scale = 1.0 + min(max(snake.length - 5, 0) * 0.015, 0.12)
        segment_radius = max(4, int(9 * size_scale))

        for i in reversed(range(segment_count)):
            seg = snake.segments[i]
            sx, sy = self._camera.world_to_screen(seg.x, seg.y)

            fade = i / max(segment_count - 1, 1)
            if i == 0:
                body_color = color
                outline_color = (
                    min(255, color[0] + 30),
                    min(255, color[1] + 30),
                    min(255, color[2] + 30),
                )
            else:
                body_color = (
                    max(0, color[0] - int(18 * fade)),
                    max(0, color[1] - int(18 * fade)),
                    max(0, color[2] - int(18 * fade)),
                )
                outline_color = (
                    min(255, body_color[0] + 20),
                    min(255, body_color[1] + 20),
                    min(255, body_color[2] + 20),
                )

            pygame.draw.circle(
                screen, body_color, (int(sx), int(sy)), segment_radius
            )
            pygame.draw.circle(
                screen, outline_color, (int(sx), int(sy)), segment_radius, 2
            )

        head = snake.segments[0]
        hx, hy = self._camera.world_to_screen(head.x, head.y)

        pygame.draw.circle(screen, color, (int(hx), int(hy)), segment_radius)

        angle_rad = math.radians(snake.direction)
        eye_offset = max(4, int(segment_radius * 0.45))
        for sign in (-1, 1):
            perp_angle = angle_rad + sign * math.pi / 2
            ex = hx + math.cos(perp_angle) * eye_offset
            ey = hy + math.sin(perp_angle) * eye_offset
            pygame.draw.circle(screen, (255, 255, 255), (int(ex), int(ey)), 2)
            px = ex + math.cos(angle_rad) * 1.5
            py = ey + math.sin(angle_rad) * 1.5
            pygame.draw.circle(screen, (10, 10, 10), (int(px), int(py)), 1)

        if snake.name:
            name_surf = self._name_font.render(snake.name, True, (220, 220, 220))
            screen.blit(
                name_surf,
                (int(hx) - name_surf.get_width() // 2, int(hy) - 28),
            )


    def _render_foods(
        self, screen: pygame.Surface, foods: list[FoodData]
    ) -> None:
        """Draw all food items as small glowing dots."""
        vis = self._camera.get_visible_rect()

        for i, food in enumerate(foods):
            if not vis.collidepoint(int(food.x), int(food.y)):
                continue

            sx, sy = self._camera.world_to_screen(food.x, food.y)
            color = FOOD_COLORS[i % len(FOOD_COLORS)]

            glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            glow_color = (*color, 50)
            pygame.draw.circle(glow_surf, glow_color, (10, 10), 8)
            screen.blit(
                glow_surf,
                (int(sx) - 10, int(sy) - 10),
                special_flags=pygame.BLEND_RGBA_ADD,
            )

            pygame.draw.circle(screen, color, (int(sx), int(sy)), 4)
