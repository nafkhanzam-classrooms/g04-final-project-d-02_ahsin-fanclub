"""
Snapshot Buffer — Maintains an ordered history of server snapshots.

Used by the SnapshotInterpolator to find bracketing snapshots for
smooth rendering between server ticks.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TimestampedSnapshot:
    """A server snapshot annotated with the local time it was received."""
    tick: int
    local_time: float
    data: dict[str, Any]


class SnapshotBuffer:
    """
    A bounded, ordered buffer of recent server snapshots.

    Snapshots are stored in arrival order (by tick).  Old snapshots are
    pruned automatically when the buffer exceeds *max_size*.

    Attributes:
        max_size: Maximum number of snapshots to retain.
    """

    def __init__(self, max_size: int = 30) -> None:
        self.max_size: int = max_size
        self._buffer: list[TimestampedSnapshot] = []

    def push(self, snapshot_data: dict[str, Any]) -> None:
        """
        Add a new snapshot from the server.

        The snapshot is timestamped with the current local time.
        Out-of-order or duplicate ticks are silently dropped.
        """
        tick: int = snapshot_data.get("tick", 0)

        # Discard out-of-order / duplicate
        if self._buffer and tick <= self._buffer[-1].tick:
            return

        ts = TimestampedSnapshot(
            tick=tick,
            local_time=time.monotonic(),
            data=snapshot_data,
        )
        self._buffer.append(ts)

        # Prune oldest
        if len(self._buffer) > self.max_size:
            self._buffer = self._buffer[-self.max_size:]

    def get_bracketing(
        self, render_time: float
    ) -> tuple[TimestampedSnapshot | None, TimestampedSnapshot | None]:
        """
        Find the two snapshots that bracket *render_time*.

        Returns (A, B) where A.local_time <= render_time <= B.local_time.
        If only one snapshot is available, it is returned as A with B=None.
        If the buffer is empty, returns (None, None).
        """
        if not self._buffer:
            return None, None

        # render_time is before our oldest snapshot
        if render_time <= self._buffer[0].local_time:
            return self._buffer[0], None

        # render_time is after our newest snapshot
        if render_time >= self._buffer[-1].local_time:
            return self._buffer[-1], None

        # Find bracketing pair
        for i in range(len(self._buffer) - 1):
            a = self._buffer[i]
            b = self._buffer[i + 1]
            if a.local_time <= render_time <= b.local_time:
                return a, b

        # Fallback — should not happen
        return self._buffer[-1], None

    @property
    def latest(self) -> TimestampedSnapshot | None:
        """Return the most recent snapshot, or None if empty."""
        return self._buffer[-1] if self._buffer else None

    @property
    def size(self) -> int:
        """Number of snapshots currently buffered."""
        return len(self._buffer)

    def clear(self) -> None:
        """Drop all buffered snapshots."""
        self._buffer.clear()
