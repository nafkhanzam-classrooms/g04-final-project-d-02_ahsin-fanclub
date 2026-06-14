"""
WebSocket Server — Accepts connections, decodes messages, and routes them.

This is the core networking entry point.  It owns the ConnectionManager,
MessageRouter, MatchmakingService, and RoomManager, wiring them together
and handling the per-client receive loop.
"""

from __future__ import annotations

import asyncio
import logging
import math
from typing import Any

import websockets
from websockets.asyncio.server import ServerConnection

from server.matchmaking.matchmaking_service import MatchmakingService
from server.networking.connection_manager import ConnectionManager
from server.networking.message_router import MessageRouter
from server.networking.packet_decoder import DecodeError, decode
from server.networking.rate_limiter import RateLimiter
from server.rooms.player_session import PlayerSession, PlayerState
from server.rooms.room import RoomState
from server.rooms.room_manager import RoomManager
from server.shared.constants import (
    MAX_MESSAGE_SIZE,
    WEBSOCKET_HOST,
    WEBSOCKET_PORT,
)
from server.shared.schemas import ErrorPayload

logger = logging.getLogger(__name__)


class WebSocketServer:
    """
    The main WebSocket server.

    Responsibilities:
    - Start and run the ``websockets`` async server.
    - Accept new connections and assign player IDs.
    - Run per-client receive loops.
    - Decode and route incoming messages.
    - Handle disconnections and cleanup.
    """

    def __init__(
        self,
        host: str = WEBSOCKET_HOST,
        port: int = WEBSOCKET_PORT,
    ) -> None:
        self._host: str = host
        self._port: int = port

        # Core components
        self._connections: ConnectionManager = ConnectionManager()
        self._rate_limiter: RateLimiter = RateLimiter()
        self._router: MessageRouter = MessageRouter(self._rate_limiter)
        self._sessions: dict[int, PlayerSession] = {}

        # Room & matchmaking (use send callback)
        self._room_manager: RoomManager = RoomManager(self._send_to_player, self._sessions)
        self._matchmaking: MatchmakingService = MatchmakingService(
            self._room_manager,
            self._sessions,
            self._send_to_player,
        )

        # Register message handlers
        self._register_handlers()

        self._server: Any = None

    # ----- Server lifecycle -----

    async def start(self) -> None:
        """Start the WebSocket server and serve forever."""
        self._server = await websockets.serve(
            self._handle_connection,
            self._host,
            self._port,
            max_size=MAX_MESSAGE_SIZE,
            close_timeout=5,
        )
        logger.info(
            "WebSocket server started on ws://%s:%d",
            self._host,
            self._port,
        )
        await self._server.wait_closed()

    async def shutdown(self) -> None:
        """Gracefully shut down the server."""
        logger.info("Shutting down server...")
        await self._room_manager.shutdown()

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Server shutdown complete")

    # ----- Connection handling -----

    async def _handle_connection(self, ws: ServerConnection) -> None:
        """
        Handle a single client connection.

        Registers the player, runs the receive loop, and cleans up on
        disconnect.
        """
        player_id = self._connections.register(ws)
        self._sessions[player_id] = PlayerSession(player_id=player_id)

        logger.info(
            "Player %d connected (total: %d)",
            player_id,
            self._connections.connected_count,
        )

        try:
            async for raw in ws:
                if isinstance(raw, bytes):
                    await self._process_message(player_id, raw)
                elif isinstance(raw, str):
                    # Fallback for text frames (shouldn't happen with msgpack)
                    import json
                    try:
                        data = json.loads(raw)
                        await self._router.route(player_id, data)
                    except json.JSONDecodeError:
                        logger.warning("Player %d: invalid JSON text frame", player_id)
        except websockets.exceptions.ConnectionClosed as exc:
            logger.info("Player %d connection closed: %s", player_id, exc)
        except Exception:
            logger.exception("Player %d: unexpected error", player_id)
        finally:
            await self._handle_disconnect(player_id)

    async def _process_message(self, player_id: int, raw: bytes) -> None:
        """Decode and route a binary message."""
        try:
            message = decode(raw)
        except DecodeError as exc:
            logger.warning("Player %d: %s", player_id, exc)
            await self._send_to_player(
                player_id,
                ErrorPayload(message="Invalid packet format").to_dict(),
            )
            return

        await self._router.route(player_id, message)

    async def _handle_disconnect(self, player_id: int) -> None:
        """Clean up when a player disconnects."""
        session = self._sessions.pop(player_id, None)

        # Remove from matchmaking queue
        await self._matchmaking.remove_player(player_id)

        # Remove from room
        await self._room_manager.remove_player_from_room(player_id)

        # Clean up connection
        self._connections.unregister(player_id)
        self._router.remove_player(player_id)

        logger.info(
            "Player %d disconnected (total: %d)",
            player_id,
            self._connections.connected_count,
        )

    # ----- Message handlers -----

    def _register_handlers(self) -> None:
        """Register all message type handlers with the router."""
        self._router.register("join_queue", self._handle_join_queue)
        self._router.register("cancel_queue", self._handle_cancel_queue)
        self._router.register("create_room", self._handle_create_room)
        self._router.register("join_room", self._handle_join_room)
        self._router.register("start_room", self._handle_start_room)
        self._router.register("leave_room", self._handle_leave_room)
        self._router.register("input", self._handle_input)
        self._router.register("ping", self._handle_ping)

    async def _handle_join_queue(self, player_id: int, message: dict[str, Any]) -> None:
        """Handle a player requesting to join the matchmaking queue."""
        username = message.get("username", "").strip()

        if not username:
            await self._send_error(player_id, "Username cannot be empty.")
            return

        if len(username) > 16:
            await self._send_error(player_id, "Username too long.")
            return
        self._sessions[player_id].name = username
        if self._sessions[player_id].room_id:
            await self._send_error(player_id, "Leave your current room first.")
            return
        
        await self._matchmaking.add_player(player_id)

    async def _handle_cancel_queue(self, player_id: int, message: dict[str, Any]) -> None:
        """Handle a player cancelling their matchmaking request."""
        await self._matchmaking.remove_player(player_id)

    async def _handle_create_room(self, player_id: int, message: dict[str, Any]) -> None:
        """Create a private room for the requesting player."""
        session = self._sessions.get(player_id)
        if session is None:
            return

        if session.room_id:
            await self._send_error(player_id, "You are already in a room.")
            return

        await self._matchmaking.remove_player(player_id)
        username = message.get("username", "").strip()
        if username:
            session.name = username[:16]

        room = self._room_manager.create_room([player_id])
        await self._room_manager.broadcast_room_state(room)

    async def _handle_join_room(self, player_id: int, message: dict[str, Any]) -> None:
        """Join an existing private room by code."""
        session = self._sessions.get(player_id)
        if session is None:
            return

        if session.room_id:
            await self._send_error(player_id, "You are already in a room.")
            return

        room_code = str(message.get("room_code", "")).strip()
        if not room_code:
            await self._send_error(player_id, "Room code cannot be empty.")
            return

        username = message.get("username", "").strip()
        if username:
            session.name = username[:16]

        await self._matchmaking.remove_player(player_id)
        room = self._room_manager.join_room(room_code, player_id)
        if room is None:
            await self._send_error(player_id, "Room not found or not joinable.")
            return

        await self._room_manager.broadcast_room_state(room)

    async def _handle_start_room(self, player_id: int, message: dict[str, Any]) -> None:
        """Start a waiting room created by the host."""
        room = self._room_manager.get_player_room(player_id)
        if room is None:
            await self._send_error(player_id, "You are not in a room.")
            return

        # instead of fragile player_ids[0] index check.
        if room.host_player_id != player_id:
            await self._send_error(player_id, "Only the host can start the room.")
            return

        if room.state.name.lower() != "waiting":
            await self._send_error(player_id, "Room is already starting or running.")
            return

        room.state = RoomState.STARTING
        await self._room_manager.broadcast_room_state(room)
        await room.start_countdown()

    async def _handle_leave_room(self, player_id: int, message: dict[str, Any]) -> None:
        """Remove the player from their current room."""
        await self._room_manager.remove_player_from_room(player_id)
        self._sessions[player_id].room_id = None
        self._sessions[player_id].state = PlayerState.CONNECTED

    async def _send_error(self, player_id: int, message: str) -> None:
        """Send an error payload to a player."""
        await self._send_to_player(player_id, ErrorPayload(message=message).to_dict())

    async def _handle_input(self, player_id: int, message: dict[str, Any]) -> None:
        """Handle a player input (direction change)."""
        direction = message.get("direction")
        if direction is None:
            return

        try:
            direction = float(direction)
        except (TypeError, ValueError):
            return

        if not math.isfinite(direction):
            return

        # Forward to the player's room
        room = self._room_manager.get_player_room(player_id)
        if room:
            room.receive_input(player_id, direction)

    async def _handle_ping(self, player_id: int, message: dict[str, Any]) -> None:
        """Respond to a ping with a pong."""
        await self._send_to_player(player_id, {"type": "pong"})

    # ----- Sending -----

    async def _send_to_player(self, player_id: int, data: dict[str, Any]) -> None:
        """Send a message to a specific player."""
        await self._connections.send_to(player_id, data)
