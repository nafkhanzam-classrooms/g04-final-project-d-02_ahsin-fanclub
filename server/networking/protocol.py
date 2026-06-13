"""
Protocol — Defines the wire protocol constants.

Re-exports message types from the shared schemas module so the
networking layer has a single import point.
"""

from __future__ import annotations

from server.shared.schemas import ClientMessageType, ServerMessageType

# Valid client message types for quick validation
VALID_CLIENT_TYPES: frozenset[str] = frozenset(t.value for t in ClientMessageType)

__all__ = [
    "ClientMessageType",
    "ServerMessageType",
    "VALID_CLIENT_TYPES",
]
