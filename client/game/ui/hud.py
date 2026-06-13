"""
HUD — Heads-Up Display overlay for the gameplay screen.

Displays:
  - Remaining time
  - Score
  - Rank / Position
  - Alive / Dead status
  - FPS counter
  - Network ping (latency)
"""

from __future__ import annotations

import pygame


# ---------------------------------------------------------------------------
# HUD styling
# ---------------------------------------------------------------------------

COLOR_HUD_BG = (15, 15, 25, 160)       # Semi-transparent dark panel
COLOR_HUD_TEXT = (220, 220, 230)
COLOR_HUD_ACCENT = (100, 200, 255)
COLOR_HUD_DANGER = (255, 80, 80)
COLOR_HUD_SUCCESS = (80, 255, 120)


class HUD:
    """
    In-game heads-up display rendered on top of the game world.

    Usage:
        hud = HUD(screen_width, screen_height)
        hud.update(time_left=87, score=120, rank=2, total=4,
                   alive=True, fps=60, ping=35.2)
        hud.render(screen)
    """

    def __init__(self, screen_width: int, screen_height: int) -> None:
        self._sw: int = screen_width
        self._sh: int = screen_height

        self._font_large: pygame.font.Font = pygame.font.SysFont(
            "Arial", 28, bold=True
        )
        self._font_medium: pygame.font.Font = pygame.font.SysFont(
            "Arial", 20, bold=True
        )
        self._font_small: pygame.font.Font = pygame.font.SysFont(
            "Arial", 14
        )

        # State
        self._time_left: int = 0
        self._score: int = 0
        self._rank: int = 0
        self._total_players: int = 0
        self._alive: bool = True
        self._fps: int = 0
        self._ping: float = 0.0

    def update(
        self,
        time_left: int = 0,
        score: int = 0,
        rank: int = 0,
        total_players: int = 0,
        alive: bool = True,
        fps: int = 0,
        ping: float = 0.0,
    ) -> None:
        """Update the HUD values."""
        self._time_left = time_left
        self._score = score
        self._rank = rank
        self._total_players = total_players
        self._alive = alive
        self._fps = fps
        self._ping = ping

    def render(self, screen: pygame.Surface) -> None:
        """Draw the HUD overlay."""
        self._render_timer(screen)
        self._render_score_panel(screen)
        self._render_debug_panel(screen)
        self._render_status(screen)

    # ----- Timer (top center) -----

    def _render_timer(self, screen: pygame.Surface) -> None:
        """Draw the countdown timer at the top center."""
        minutes = self._time_left // 60
        seconds = self._time_left % 60
        time_str = f"{minutes:01d}:{seconds:02d}"

        # Danger color when low
        color = COLOR_HUD_DANGER if self._time_left <= 10 else COLOR_HUD_ACCENT

        text_surf = self._font_large.render(time_str, True, color)

        # Background panel
        panel_w = text_surf.get_width() + 30
        panel_h = text_surf.get_height() + 12
        panel_rect = pygame.Rect(
            self._sw // 2 - panel_w // 2, 10,
            panel_w, panel_h,
        )
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(COLOR_HUD_BG)
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, (60, 70, 100), panel_rect, 1, border_radius=6)

        screen.blit(
            text_surf,
            (
                panel_rect.centerx - text_surf.get_width() // 2,
                panel_rect.centery - text_surf.get_height() // 2,
            ),
        )

    # ----- Score & rank (top left) -----

    def _render_score_panel(self, screen: pygame.Surface) -> None:
        """Draw the score and rank panel at the top left."""
        panel_w, panel_h = 180, 65
        panel_rect = pygame.Rect(10, 10, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(COLOR_HUD_BG)
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, (60, 70, 100), panel_rect, 1, border_radius=6)

        # Score
        score_surf = self._font_medium.render(
            f"Score: {self._score}", True, COLOR_HUD_TEXT
        )
        screen.blit(score_surf, (20, 16))

        # Rank
        rank_str = f"Rank: #{self._rank}/{self._total_players}"
        rank_surf = self._font_small.render(rank_str, True, COLOR_HUD_ACCENT)
        screen.blit(rank_surf, (20, 46))

    # ----- Debug panel — FPS & Ping (top right) -----

    def _render_debug_panel(self, screen: pygame.Surface) -> None:
        """Draw FPS and ping at the top right."""
        panel_w, panel_h = 140, 50
        panel_rect = pygame.Rect(self._sw - panel_w - 10, 10, panel_w, panel_h)
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(COLOR_HUD_BG)
        screen.blit(panel_surf, panel_rect.topleft)
        pygame.draw.rect(screen, (60, 70, 100), panel_rect, 1, border_radius=6)

        # FPS
        fps_color = COLOR_HUD_SUCCESS if self._fps >= 55 else COLOR_HUD_DANGER
        fps_surf = self._font_small.render(
            f"FPS: {self._fps}", True, fps_color
        )
        screen.blit(fps_surf, (self._sw - panel_w, 16))

        # Ping
        ping_color = (
            COLOR_HUD_SUCCESS if self._ping < 80
            else COLOR_HUD_DANGER
        )
        ping_surf = self._font_small.render(
            f"Ping: {self._ping:.0f}ms", True, ping_color
        )
        screen.blit(ping_surf, (self._sw - panel_w, 36))

    # ----- Alive / Dead status (bottom center) -----

    def _render_status(self, screen: pygame.Surface) -> None:
        """Draw alive/dead status indicator at the bottom center."""
        if self._alive:
            return  # Don't clutter the screen when alive

        text = "YOU DIED"
        text_surf = self._font_large.render(text, True, COLOR_HUD_DANGER)

        # Dim background
        overlay = pygame.Surface((self._sw, 60), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        screen.blit(overlay, (0, self._sh // 2 - 30))

        screen.blit(
            text_surf,
            (
                self._sw // 2 - text_surf.get_width() // 2,
                self._sh // 2 - text_surf.get_height() // 2,
            ),
        )
