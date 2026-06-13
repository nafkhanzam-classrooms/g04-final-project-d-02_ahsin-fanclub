"""
GameApp — Central application class.

Owns the Pygame window, clock, scene manager, network client, and
event dispatcher.  Orchestrates the main async game loop:

    poll events → update active scene → render → flip display
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import pygame

from game.networking.event_dispatcher import EventDispatcher
from game.networking.websocket_client import WebSocketClient
from game.scene_manager import SceneManager

# Import all scene classes for registration
from game.scenes.menu_scene import MenuScene
from game.scenes.matchmaking_scene import MatchmakingScene
from game.scenes.loading_scene import LoadingScene
from game.scenes.gameplay_scene import GameplayScene
from game.scenes.results_scene import ResultsScene

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Window configuration
# ---------------------------------------------------------------------------

SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
WINDOW_TITLE: str = "Snake.io — Multiplayer Arena"
TARGET_FPS: int = 60


class GameApp:
    """
    The main application controller.

    Manages the Pygame window, main loop, and all shared subsystems
    (networking, event dispatch, scene management).

    The main loop is async so that WebSocket I/O and the render loop
    can coexist on the same thread via asyncio cooperative scheduling.
    """

    def __init__(self) -> None:
        # Pygame display
        self._screen: pygame.Surface = pygame.display.set_mode(
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            pygame.DOUBLEBUF,
        )
        pygame.display.set_caption(WINDOW_TITLE)
        self._clock: pygame.time.Clock = pygame.time.Clock()

        # Shared subsystems
        self._event_dispatcher: EventDispatcher = EventDispatcher()
        self._network_client: WebSocketClient = WebSocketClient(self._event_dispatcher)
        self._scene_manager: SceneManager = SceneManager(self)

        # Register all scenes
        self._scene_manager.register("menu", MenuScene)
        self._scene_manager.register("matchmaking", MatchmakingScene)
        self._scene_manager.register("loading", LoadingScene)
        self._scene_manager.register("gameplay", GameplayScene)
        self._scene_manager.register("results", ResultsScene)

        # Shared state between scenes
        self.match_data: dict[str, Any] = {}
        self.match_results: dict[str, Any] = {}
        self._running: bool = False

    # ----- Properties -----

    @property
    def screen_size(self) -> tuple[int, int]:
        """Window dimensions."""
        return (SCREEN_WIDTH, SCREEN_HEIGHT)

    @property
    def scene_manager(self) -> SceneManager:
        return self._scene_manager

    @property
    def network_client(self) -> WebSocketClient:
        return self._network_client

    @property
    def event_dispatcher(self) -> EventDispatcher:
        return self._event_dispatcher

    # ----- Main loop -----

    async def run(self) -> None:
        """
        Async main game loop.

        Uses `asyncio.sleep(0)` to yield control to the event loop
        between frames, allowing the WebSocket receive loop to process
        incoming messages.
        """
        self._running = True

        # Start on the main menu
        self._scene_manager.switch("menu")

        while self._running:
            # Delta time in seconds
            dt = self._clock.tick(TARGET_FPS) / 1000.0

            # --- Event polling ---
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._running = False
                    break
                self._scene_manager.handle_event(event)

            if not self._running:
                break

            # --- Update ---
            self._scene_manager.update(dt)

            # --- Render ---
            self._scene_manager.render(self._screen)
            pygame.display.flip()

            # Yield to asyncio event loop (lets WebSocket recv run)
            await asyncio.sleep(0)

    async def shutdown(self) -> None:
        """Clean up resources on exit."""
        logger.info("Shutting down...")
        self._running = False

        await self._network_client.close()
        self._event_dispatcher.clear()

        logger.info("Shutdown complete")
