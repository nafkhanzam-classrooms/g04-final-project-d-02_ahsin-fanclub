"""
Network protocol constants and message encoding/decoding.

All communication uses msgpack for binary serialization over WebSocket.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

import msgpack


# ---------------------------------------------------------------------------
# Message Types — Client → Server
# ---------------------------------------------------------------------------

class ClientMessageType(str, Enum):
    """Messages the client can send to the server."""
    INPUT = "input"
    JOIN_QUEUE = "join_queue"
    CANCEL_QUEUE = "cancel_queue"


# ---------------------------------------------------------------------------
# Message Types — Server → Client
# ---------------------------------------------------------------------------

class ServerMessageType(str, Enum):
    """Messages the server can send to the client."""
    SNAPSHOT = "snapshot"
    MATCH_FOUND = "match_found"
    MATCH_START = "match_start"
    PLAYER_ELIMINATED = "player_eliminated"
    MATCH_END = "match_end"
    QUEUE_STATUS = "queue_status"
    ERROR = "error"


# ---------------------------------------------------------------------------
# Encoding helpers
# ---------------------------------------------------------------------------

def encode_message(data: dict[str, Any]) -> bytes:
    """Encode a Python dict to msgpack bytes for transmission."""
    return msgpack.packb(data, use_bin_type=True)


def decode_message(raw: bytes) -> dict[str, Any]:
    """Decode msgpack bytes received from the server into a Python dict."""
    return msgpack.unpackb(raw, raw=False)


# ---------------------------------------------------------------------------
# Convenience constructors — Client messages
# ---------------------------------------------------------------------------

def make_input_message(direction: float) -> bytes:
    """Create an encoded input message with the given direction angle (degrees)."""
    return encode_message({
        "type": ClientMessageType.INPUT.value,
        "direction": direction,
    })


def make_join_queue_message(username: str) -> bytes:
    """Create an encoded join-queue request."""
    return encode_message({
        "type": ClientMessageType.JOIN_QUEUE.value,
        "username": username
    })


def make_cancel_queue_message() -> bytes:
    """Create an encoded cancel-queue request."""
    return encode_message({
        "type": ClientMessageType.CANCEL_QUEUE.value,
    })
