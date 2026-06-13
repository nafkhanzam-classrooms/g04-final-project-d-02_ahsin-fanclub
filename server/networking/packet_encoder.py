"""
Packet Encoder — Serializes Python dicts to msgpack bytes for transmission.

All outgoing server messages pass through this encoder before being sent
over the WebSocket.
"""

from __future__ import annotations

from typing import Any

import msgpack


def encode(data: dict[str, Any]) -> bytes:
    """
    Encode a Python dict to msgpack binary format.

    Args:
        data: The message payload as a dict.

    Returns:
        msgpack-encoded bytes ready for WebSocket transmission.
    """
    return msgpack.packb(data, use_bin_type=True)
