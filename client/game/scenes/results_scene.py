"""
Results Scene — Displayed after a match ends.

Shows the winner, final ranking, scores for all players, and
a button to return to the main menu.
"""

from __future__ import annotations

import time
from typing import Any, TYPE_CHECKING

import pygame

from game.scene_manager import Scene
from game.ui.widgets import Button, Label

if TYPE_CHECKING:
    from game.game_app import GameApp


# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------

COLOR_BG = (10, 10, 24)
COLOR_GOLD = (255, 215, 0)
COLOR_SILVER = (192, 192, 200)
COLOR_BRONZE = (205, 127, 50)
COLOR_TEXT = (200, 200, 210)
COLOR_WINNER = (80, 255, 160)
COLOR_ACCENT = (100, 150, 255)

RANK_COLORS = [COLOR_GOLD, COLOR_SILVER, COLOR_BRONZE]


class ResultsScene(Scene):
    """Results screen — winner, ranking, scores, return to menu."""

    def __init__(self, app: "GameApp") -> None:
        super().__init__(app)
        sw, sh = app.screen_size

        self._title = Label(
            "MATCH RESULTS",
            x=sw // 2,
            y=60,
            color=COLOR_ACCENT,
            font_size=40,
            centered=True,
            bold=True,
        )

        btn_w, btn_h = 240, 55
        self._menu_btn = Button(
            x=sw // 2 - btn_w // 2,
            y=sh - 100,
            width=btn_w,
            height=btn_h,
            text="RETURN TO MENU",
            on_click=self._on_return_menu,
            font_size=20,
        )

        # Match data (populated in enter())
        self._winner_name: str = ""
        self._rankings: list[dict[str, Any]] = []
        self._local_player_id: int = -1

    # ----- Lifecycle -----

    def enter(self) -> None:
        """Extract match results data."""
        results = getattr(self.app, "match_results", {})

        self._winner_name = results.get("winner_name", "Unknown")
        self._rankings = results.get("rankings", [])
        self._local_player_id = results.get("local_player_id", -1)

        # If no rankings provided, try to build from available data
        if not self._rankings:
            # Fallback: create dummy entries
            self._rankings = [
                {"name": self._winner_name, "score": 0, "id": -1}
            ]

    def exit(self) -> None:
        pass

    # ----- Events -----

    def handle_event(self, event: pygame.event.Event) -> None:
        self._menu_btn.handle_event(event)

    def update(self, dt: float) -> None:
        pass  # Static screen

    # ----- Render -----

    def render(self, screen: pygame.Surface) -> None:
        screen.fill(COLOR_BG)
        sw, sh = screen.get_size()

        self._title.render(screen)

        # Winner announcement
        winner_font = pygame.font.SysFont("Arial", 32, bold=True)
        winner_surf = winner_font.render(
            f"🏆  Winner: {self._winner_name}", True, COLOR_WINNER
        )
        screen.blit(
            winner_surf,
            (sw // 2 - winner_surf.get_width() // 2, 130),
        )

        # Rankings table
        self._render_rankings(screen, sw, sh)

        self._menu_btn.render(screen)

    def _render_rankings(
        self, screen: pygame.Surface, sw: int, sh: int
    ) -> None:
        """Draw the ranking table."""
        header_font = pygame.font.SysFont("Arial", 18, bold=True)
        row_font = pygame.font.SysFont("Arial", 20)

        table_top = 200
        row_height = 45
        col_rank_x = sw // 2 - 200
        col_name_x = sw // 2 - 120
        col_score_x = sw // 2 + 120

        # Header
        header_color = (120, 130, 160)
        for text, x in [("RANK", col_rank_x), ("PLAYER", col_name_x), ("SCORE", col_score_x)]:
            surf = header_font.render(text, True, header_color)
            screen.blit(surf, (x, table_top))

        # Separator line
        pygame.draw.line(
            screen, (40, 45, 70),
            (col_rank_x, table_top + 28),
            (col_score_x + 80, table_top + 28),
            1,
        )

        # Rows
        for i, entry in enumerate(self._rankings):
            y = table_top + 40 + i * row_height
            rank = i + 1
            name = entry.get("name", f"Player {entry.get('id', '?')}")
            score = entry.get("score", 0)
            player_id = entry.get("id", -1)

            # Color based on rank
            if rank <= 3:
                color = RANK_COLORS[rank - 1]
            else:
                color = COLOR_TEXT

            # Highlight local player
            if player_id == self._local_player_id:
                highlight = pygame.Surface((420, row_height - 5), pygame.SRCALPHA)
                highlight.fill((50, 60, 100, 60))
                screen.blit(highlight, (col_rank_x - 10, y - 5))

            rank_str = f"#{rank}"
            rank_surf = row_font.render(rank_str, True, color)
            screen.blit(rank_surf, (col_rank_x, y))

            name_surf = row_font.render(name, True, color)
            screen.blit(name_surf, (col_name_x, y))

            score_surf = row_font.render(str(score), True, color)
            screen.blit(score_surf, (col_score_x, y))

    # ----- Callbacks -----

    def _on_return_menu(self) -> None:
        """Return to the main menu and disconnect."""
        import asyncio
        asyncio.ensure_future(self.app.network_client.close())
        self.app.scene_manager.switch("menu")
