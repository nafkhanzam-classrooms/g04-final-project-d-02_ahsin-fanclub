"""
Room — Represents a single game room/match.

Contains the player roster, room state machine, and the game simulation
reference.  The room is responsible for running the game loop and
broadcasting snapshots to its players.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from server.shared.constants import (
    MATCH_DURATION,
    MATCH_START_COUNTDOWN,
    MAX_PLAYERS_PER_ROOM,
    SERVER_TICK_RATE,
    TICK_INTERVAL,
)
from server.shared.schemas import (
    MatchEndPayload,
    MatchFoundPayload,
    MatchStartPayload,
    PlayerEliminatedPayload,
    SnapshotPayload,
    SnapshotSnake,
    SnapshotFood,
)
from server.simulation.game_world import GameWorld

logger = logging.getLogger(__name__)


class RoomState(Enum):
    """Room lifecycle states."""
    WAITING = auto()
    STARTING = auto()
    RUNNING = auto()
    FINISHED = auto()


@dataclass
class Room:
    """
    A game room containing 2–4 players and a game simulation.

    Attributes:
        room_id:     Unique room identifier.
        player_ids:  Set of player IDs in this room.
        state:       Current room state.
    """

    room_id: str
    player_ids: list[int] = field(default_factory=list)
    state: RoomState = RoomState.WAITING
    host_player_id: int = -1
    _game_world: GameWorld | None = field(default=None, init=False, repr=False)
    _game_task: asyncio.Task[None] | None = field(default=None, init=False, repr=False)

    _send_callback: Any = field(default=None, init=False, repr=False)
    _finish_callback: Any = field(default=None, init=False, repr=False)
    _player_names: dict[int, str] = field(default_factory=dict, init=False, repr=False)


    def add_player(self, player_id: int, name: str = "") -> None:
        """Add a player to the room."""
        if player_id not in self.player_ids:
            self.player_ids.append(player_id)
            self._player_names[player_id] = name or f"Player {player_id}"
            if self.host_player_id == -1:
                self.host_player_id = player_id

    def remove_player(self, player_id: int) -> None:
        """Remove a player from the room."""
        if player_id in self.player_ids:
            self.player_ids.remove(player_id)
            self._player_names.pop(player_id, None)
            if self.host_player_id == player_id:
                self.host_player_id = self.player_ids[0] if self.player_ids else -1

        if self._game_world and self.state == RoomState.RUNNING:
            self._game_world.remove_player(player_id)

    @property
    def player_count(self) -> int:
        """Number of players in the room."""
        return len(self.player_ids)

    @property
    def is_full(self) -> bool:
        """Whether the room has reached max capacity."""
        return self.player_count >= MAX_PLAYERS_PER_ROOM


    def set_send_callback(self, callback: Any) -> None:
        """Set the async callback for sending messages to players."""
        self._send_callback = callback

    def set_finish_callback(self, callback: Any) -> None:
        """Set the callback for when the room finishes."""
        self._finish_callback = callback

    async def start_countdown(self) -> None:
        """
        Begin the match start countdown.

        Sends MATCH_FOUND immediately, then waits for MATCH_START_COUNTDOWN
        seconds before starting the game loop.
        """
        self.state = RoomState.STARTING

        match_found = MatchFoundPayload(
            room_id=self.room_id,
            player_count=self.player_count,
        ).to_dict()

        for pid in self.player_ids:
            if self._send_callback:
                await self._send_callback(pid, match_found)

        await asyncio.sleep(MATCH_START_COUNTDOWN)

        match_start = MatchStartPayload(room_id=self.room_id).to_dict()
        for pid in self.player_ids:
            if self._send_callback:
                await self._send_callback(pid, match_start)

        await self._start_game()

    async def _start_game(self) -> None:
        """Initialize the game simulation and start the game loop."""
        self.state = RoomState.RUNNING

        self._game_world = GameWorld()
        for pid in self.player_ids:
            name = self._player_names.get(pid, f"Player {pid}")
            self._game_world.add_player(pid, name)

        self._game_world.initialize()

        self._game_task = asyncio.create_task(self._game_loop())
        logger.info("Room %s: game started with %d players", self.room_id, self.player_count)

    async def _game_loop(self) -> None:
        """
        Fixed-timestep game loop running at SERVER_TICK_RATE.

        Each tick:
        1. Update the simulation
        2. Check for eliminations
        3. Check win conditions
        4. Generate and broadcast snapshots
        """
        assert self._game_world is not None

        try:
            while self.state == RoomState.RUNNING:
                tick_start = time.monotonic()

                self._game_world.update(TICK_INTERVAL)

                eliminations = self._game_world.get_pending_eliminations()
                for elim_pid in eliminations:
                    payload = PlayerEliminatedPayload(player_id=elim_pid).to_dict()
                    for pid in self.player_ids:
                        if self._send_callback:
                            await self._send_callback(pid, payload)

                result = self._game_world.check_win_condition()
                if result is not None:
                    await self._end_match(result)
                    return

                snapshot_base = self._game_world.get_snapshot()
                for pid in self.player_ids:
                    snapshot = dict(snapshot_base)
                    snapshot["local_player_id"] = pid
                    if self._send_callback:
                        await self._send_callback(pid, snapshot)

                elapsed = time.monotonic() - tick_start
                sleep_time = TICK_INTERVAL - elapsed
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            logger.info("Room %s: game loop cancelled", self.room_id)
        except Exception:
            logger.exception("Room %s: game loop error", self.room_id)
        finally:
            if self.state == RoomState.RUNNING:
                self.state = RoomState.FINISHED

    async def _end_match(self, result: dict[str, Any]) -> None:
        """End the match and broadcast results."""
        self.state = RoomState.FINISHED

        payload = MatchEndPayload(
            winner_id=result.get("winner_id", -1),
            winner_name=result.get("winner_name", "Unknown"),
            rankings=result.get("rankings", []),
        ).to_dict()

        for pid in self.player_ids:
            per_player = dict(payload)
            per_player["local_player_id"] = pid
            if self._send_callback:
                await self._send_callback(pid, per_player)

        logger.info(
            "Room %s: match ended — winner: %s",
            self.room_id,
            result.get("winner_name", "Unknown"),
        )

        if self._finish_callback:
            await self._finish_callback(self.room_id)


    def receive_input(self, player_id: int, direction: float) -> None:
        """Forward a player's direction input to the simulation."""
        if self._game_world and self.state == RoomState.RUNNING:
            self._game_world.receive_input(player_id, direction)


    async def destroy(self) -> None:
        """Cancel the game loop and clean up resources."""
        if self._game_task and not self._game_task.done():
            self._game_task.cancel()
            try:
                await self._game_task
            except asyncio.CancelledError:
                pass
        self._game_world = None
        self.state = RoomState.FINISHED
        logger.info("Room %s: destroyed", self.room_id)
