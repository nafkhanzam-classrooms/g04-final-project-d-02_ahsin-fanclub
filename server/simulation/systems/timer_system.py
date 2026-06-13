"""
Timer System — Match countdown timer.

Tracks elapsed time and determines when the match duration expires.
"""

from __future__ import annotations

from server.shared.constants import MATCH_DURATION


class TimerSystem:
    """
    Match timer with configurable duration.

    Counts down from ``duration`` to zero.
    """

    def __init__(self, duration: int = MATCH_DURATION) -> None:
        self._duration: int = duration
        self._elapsed: float = 0.0

    @property
    def time_left(self) -> int:
        """Remaining time in whole seconds."""
        remaining = self._duration - self._elapsed
        return max(0, int(remaining))

    @property
    def expired(self) -> bool:
        """Whether the timer has reached zero."""
        return self._elapsed >= self._duration

    def update(self, dt: float) -> None:
        """Advance the timer by *dt* seconds."""
        self._elapsed += dt

    def reset(self, duration: int | None = None) -> None:
        """Reset the timer, optionally with a new duration."""
        self._elapsed = 0.0
        if duration is not None:
            self._duration = duration
