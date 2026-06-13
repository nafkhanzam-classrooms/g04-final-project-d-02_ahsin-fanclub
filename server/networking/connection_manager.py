"""
Connection Manager — Tracks connected WebSocket clients.

Assigns unique player IDs, maps them to WebSocket connections, and
handles cleanup on disconnect.
"""

from __future__ import annotations

import itertools
import logging
from typing import Any

from websockets.asyncio.server import ServerConnection

from server.networking.packet_encoder import encode

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages the mapping between player IDs and their WebSocket connections.

    Thread-safe is not required because we run on a single-threaded
    asyncio event loop.
    """

    def __init__(self) -> None:
        self._id_counter = itertools.count(start=1)
        self._connections: dict[int, ServerConnection] = {}
        self._ws_to_id: dict[ServerConnection, int] = {}

    # ----- Registration -----

    def register(self, ws: ServerConnection) -> int:
        """
        Register a new WebSocket connection and assign a player ID.

        Returns:
            The newly assigned player ID.
        """
        player_id = next(self._id_counter)
        self._connections[player_id] = ws
        self._ws_to_id[ws] = player_id
        logger.info("Player %d connected", player_id)
        return player_id

    def unregister(self, player_id: int) -> None:
        """Remove a player's connection mapping."""
        ws = self._connections.pop(player_id, None)
        if ws is not None:
            self._ws_to_id.pop(ws, None)
        logger.info("Player %d disconnected", player_id)

    # ----- Lookups -----

    def get_ws(self, player_id: int) -> ServerConnection | None:
        """Get the WebSocket for a player ID."""
        return self._connections.get(player_id)

    def get_player_id(self, ws: ServerConnection) -> int | None:
        """Get the player ID for a WebSocket."""
        return self._ws_to_id.get(ws)

    def is_connected(self, player_id: int) -> bool:
        """Check if a player is currently connected."""
        return player_id in self._connections

    @property
    def connected_count(self) -> int:
        """Number of currently connected players."""
        return len(self._connections)

    # ----- Sending -----

    async def send_to(self, player_id: int, data: dict[str, Any]) -> None:
        """
        Send a message to a specific player.

        Silently drops the message if the player is not connected.
        """
        ws = self._connections.get(player_id)
        if ws is None:
            return
        try:
            await ws.send(encode(data))
        except Exception as exc:
            logger.warning("Send to player %d failed: %s", player_id, exc)

    async def send_to_many(
        self, player_ids: list[int], data: dict[str, Any]
    ) -> None:
        """Send the same message to multiple players."""
        encoded = encode(data)
        for pid in player_ids:
            ws = self._connections.get(pid)
            if ws is None:
                continue
            try:
                await ws.send(encoded)
            except Exception as exc:
                logger.warning("Send to player %d failed: %s", pid, exc)

    async def broadcast(self, data: dict[str, Any]) -> None:
        """Send a message to all connected players."""
        await self.send_to_many(list(self._connections.keys()), data)
