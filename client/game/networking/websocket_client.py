"""
WebSocket Client — Async networking layer.

Handles connection lifecycle, sending player input, and receiving
server messages.  Dispatches decoded messages through the EventDispatcher.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import websockets
from websockets.asyncio.client import ClientConnection

from game.networking.event_dispatcher import EventDispatcher
from game.networking.protocol import (
    ServerMessageType,
    decode_message,
    encode_message,
)

logger = logging.getLogger(__name__)

DEFAULT_SERVER_URI = "ws://localhost:8765"


class WebSocketClient:
    """
    Async WebSocket client for communicating with the game server.

    The client runs a background receive loop that decodes incoming
    msgpack messages and dispatches them through the provided
    EventDispatcher.

    Usage:
        client = WebSocketClient(dispatcher)
        await client.connect("ws://localhost:8765")
        await client.send(some_bytes)
        ...
        await client.close()
    """

    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher: EventDispatcher = dispatcher
        self._ws: ClientConnection | None = None
        self._recv_task: asyncio.Task[None] | None = None
        self._connected: bool = False
        self._ping_ms: float = 0.0
        self._ping_send_time: float = 0.0
        self._ping_task: asyncio.Task[None] | None = None
        self._server_uri: str = DEFAULT_SERVER_URI


    @property
    def connected(self) -> bool:
        """Whether the WebSocket is currently connected."""
        return self._connected

    @property
    def ping_ms(self) -> float:
        """Latest measured round-trip latency in milliseconds."""
        return self._ping_ms


    async def connect(self, uri: str | None = None) -> bool:
        """
        Open a WebSocket connection to the server.

        Returns True on success, False on failure.
        """
        if self._connected and self._ws is not None:
            return True

        self._server_uri = uri or DEFAULT_SERVER_URI

        try:
            if self._recv_task and not self._recv_task.done():
                self._recv_task.cancel()
                try:
                    await self._recv_task
                except asyncio.CancelledError:
                    pass

            if self._ws is not None:
                try:
                    await self._ws.close()
                except Exception:
                    pass

            self._ws = await websockets.connect(
                self._server_uri,
                max_size=2**20,
                close_timeout=5,
            )
            self._connected = True
            self._recv_task = asyncio.create_task(self._recv_loop())
            self._ping_task = asyncio.create_task(self._ping_loop())
            logger.info("Connected to %s", self._server_uri)
            return True
        except (OSError, websockets.exceptions.WebSocketException) as exc:
            logger.error("Connection failed: %s", exc)
            self._connected = False
            self._dispatcher.dispatch("error", {"message": f"Connection failed: {exc}"})
            return False

    async def close(self) -> None:
        """Gracefully close the connection."""
        self._connected = False
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        if self._recv_task and not self._recv_task.done():
            self._recv_task.cancel()
            try:
                await self._recv_task
            except asyncio.CancelledError:
                pass
        if self._ws:
            try:
                await self._ws.close()
            except Exception:
                pass
        self._ws = None
        logger.info("Disconnected from server")


    async def send(self, data: bytes) -> None:
        """Send raw bytes (msgpack-encoded) to the server."""
        if not self._connected or not self._ws:
            logger.warning("Cannot send — not connected")
            return
        try:
            await self._ws.send(data)
        except websockets.exceptions.WebSocketException as exc:
            logger.error("Send error: %s", exc)
            await self._handle_disconnect()

    async def send_dict(self, payload: dict[str, Any]) -> None:
        """Convenience: encode a dict to msgpack and send."""
        await self.send(encode_message(payload))


    async def _recv_loop(self) -> None:
        """
        Background task that continuously reads from the WebSocket
        and dispatches decoded messages to the EventDispatcher.
        """
        assert self._ws is not None

        try:
            async for raw in self._ws:
                if isinstance(raw, bytes):
                    message = decode_message(raw)
                elif isinstance(raw, str):
                    import json
                    message = json.loads(raw)
                else:
                    continue

                msg_type = message.get("type", "unknown")

                if msg_type == "pong" and self._ping_send_time > 0:
                    self._ping_ms = (time.monotonic() - self._ping_send_time) * 1000.0
                    self._ping_send_time = 0.0
                    continue

                self._dispatcher.dispatch(msg_type, message)

        except websockets.exceptions.ConnectionClosed as exc:
            logger.warning("Connection closed: %s", exc)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            logger.exception("Unexpected error in recv loop: %s", exc)
        finally:
            await self._handle_disconnect()

    async def _handle_disconnect(self) -> None:
        """Handle unexpected disconnection."""
        was_connected = self._connected
        self._connected = False
        self._ws = None
        self._recv_task = None
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
        self._ping_task = None
        if was_connected:
            self._dispatcher.dispatch(
                "error",
                {"message": "Lost connection to server"},
            )

    async def _ping_loop(self) -> None:
        """Send a PING to the server every 2 seconds for RTT measurement."""
        try:
            while self._connected:
                await asyncio.sleep(2.0)
                if self._connected and self._ws:
                    self._ping_send_time = time.monotonic()
                    await self._ws.send(encode_message({"type": "ping"}))
        except asyncio.CancelledError:
            pass
        except Exception:
            pass
