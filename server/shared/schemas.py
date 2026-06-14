"""
Shared data schemas for server ↔ client protocol messages.

These dataclasses provide typed, validated representations of every
message that flows through the system.  They are used by the packet
encoder/decoder and the message router.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any



class ClientMessageType(str, Enum):
    """Messages the client may send."""
    JOIN_QUEUE = "join_queue"
    LEAVE_QUEUE = "cancel_queue"
    INPUT = "input"
    PING = "ping"
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    START_ROOM = "start_room"
    LEAVE_ROOM = "leave_room"



class ServerMessageType(str, Enum):
    """Messages the server may send."""
    QUEUE_STATUS = "queue_status"
    MATCH_FOUND = "match_found"
    MATCH_START = "match_start"
    ROOM_STATE = "room_state"
    SNAPSHOT = "snapshot"
    PLAYER_ELIMINATED = "player_eliminated"
    MATCH_END = "match_end"
    PONG = "pong"
    ERROR = "error"



@dataclass
class QueueStatusPayload:
    players_waiting: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.QUEUE_STATUS.value,
            "players_waiting": self.players_waiting,
        }


@dataclass
class MatchFoundPayload:
    room_id: str
    player_count: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.MATCH_FOUND.value,
            "room_id": self.room_id,
            "player_count": self.player_count,
        }


@dataclass
class MatchStartPayload:
    room_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.MATCH_START.value,
            "room_id": self.room_id,
        }


@dataclass
class RoomPlayer:
    player_id: int
    name: str
    is_host: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "player_id": self.player_id,
            "name": self.name,
            "is_host": self.is_host,
        }


@dataclass
class RoomStatePayload:
    room_id: str
    state: str
    players: list[RoomPlayer] = field(default_factory=list)
    host_player_id: int = -1
    can_start: bool = False
    player_count: int = 0
    max_players: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.ROOM_STATE.value,
            "room_id": self.room_id,
            "state": self.state,
            "players": [player.to_dict() for player in self.players],
            "host_player_id": self.host_player_id,
            "can_start": self.can_start,
            "player_count": self.player_count,
            "max_players": self.max_players,
        }


@dataclass
class SnapshotSegment:
    x: float
    y: float

    def to_dict(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y}


@dataclass
class SnapshotSnake:
    id: int
    x: float
    y: float
    length: int
    score: int
    alive: bool
    direction: float = 0.0
    segments: list[SnapshotSegment] = field(default_factory=list)
    name: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "length": self.length,
            "score": self.score,
            "alive": self.alive,
            "direction": self.direction,
            "segments": [s.to_dict() for s in self.segments],
            "name": self.name,
        }


@dataclass
class SnapshotFood:
    x: float
    y: float

    def to_dict(self) -> dict[str, Any]:
        return {"x": self.x, "y": self.y}


@dataclass
class SnapshotPayload:
    """
    Per-player snapshot.

    The ``local_player_id`` field is set individually for each recipient
    so the client knows which snake belongs to it.
    """
    tick: int
    time_left: int
    snakes: list[SnapshotSnake] = field(default_factory=list)
    foods: list[SnapshotFood] = field(default_factory=list)
    local_player_id: int = -1

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.SNAPSHOT.value,
            "tick": self.tick,
            "time_left": self.time_left,
            "snakes": [s.to_dict() for s in self.snakes],
            "foods": [f.to_dict() for f in self.foods],
            "local_player_id": self.local_player_id,
        }


@dataclass
class PlayerEliminatedPayload:
    player_id: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.PLAYER_ELIMINATED.value,
            "player_id": self.player_id,
        }


@dataclass
class MatchEndPayload:
    winner_id: int
    winner_name: str
    rankings: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.MATCH_END.value,
            "winner_id": self.winner_id,
            "winner_name": self.winner_name,
            "rankings": self.rankings,
        }


@dataclass
class ErrorPayload:
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": ServerMessageType.ERROR.value,
            "message": self.message,
        }
