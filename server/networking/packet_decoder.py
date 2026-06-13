"""
Packet Decoder — Deserializes incoming msgpack bytes to Python dicts.

All incoming client messages are decoded through this module before
being routed to handlers.
"""

from __future__ import annotations

import logging
from typing import Any

import msgpack

logger = logging.getLogger(__name__)


class DecodeError(Exception):
    """Raised when a packet cannot be decoded."""


def decode(raw: bytes) -> dict[str, Any]:
    """
    Decode msgpack bytes into a Python dict.

    Args:
        raw: Raw bytes received from the WebSocket.

    Returns:
        Decoded message as a dict.

    Raises:
        DecodeError: If the data is not valid msgpack or not a dict.
    """
    try:
        result = msgpack.unpackb(raw, raw=False)
    except (msgpack.UnpackException, ValueError) as exc:
        raise DecodeError(f"Invalid msgpack data: {exc}") from exc

    if not isinstance(result, dict):
        raise DecodeError(f"Expected dict, got {type(result).__name__}")

    return result
