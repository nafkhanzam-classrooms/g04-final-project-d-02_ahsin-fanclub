"""
Snake.io Client — Entry Point

Initializes Pygame, creates the GameApp, and runs the async main loop.
"""

import asyncio
import sys

import pygame

from game.game_app import GameApp


async def main() -> None:
    """Entry point for the Snake.io client."""
    pygame.init()
    pygame.mixer.init()

    app = GameApp()

    try:
        await app.run()
    except KeyboardInterrupt:
        pass
    finally:
        await app.shutdown()
        pygame.quit()
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
