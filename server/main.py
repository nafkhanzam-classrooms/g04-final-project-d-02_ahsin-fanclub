"""
Snake.io Server — Entry Point

Starts the WebSocket game server with asyncio.

Usage:
    python -m server.main
    python server/main.py
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from server.networking.websocket_server import WebSocketServer
from server.shared.constants import WEBSOCKET_HOST, WEBSOCKET_PORT


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    """Entry point for the Snake.io game server."""
    server = WebSocketServer(host=WEBSOCKET_HOST, port=WEBSOCKET_PORT)

    loop = asyncio.get_running_loop()

    def _signal_handler() -> None:
        logger.info("Received shutdown signal")
        asyncio.create_task(server.shutdown())

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, _signal_handler)
        except NotImplementedError:
            pass

    logger.info(
        "Starting Snake.io server on ws://%s:%d",
        WEBSOCKET_HOST,
        WEBSOCKET_PORT,
    )
    logger.info("Press Ctrl+C to stop")

    try:
        await server.start()
    except asyncio.CancelledError:
        pass
    finally:
        await server.shutdown()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
        sys.exit(0)
