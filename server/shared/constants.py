"""
Shared constants for the Snake.io game server.

All tunable parameters are defined here for easy balancing and
configuration.  Modules should import from this file rather than
hardcoding magic numbers.
"""

from __future__ import annotations

# =============================================================================
# World
# =============================================================================

WORLD_WIDTH: int = 4000
WORLD_HEIGHT: int = 4000

# =============================================================================
# Server tick rate
# =============================================================================

SERVER_TICK_RATE: int = 30  # ticks per second
TICK_INTERVAL: float = 1.0 / SERVER_TICK_RATE  # seconds between ticks

# =============================================================================
# Room & Matchmaking
# =============================================================================

MIN_PLAYERS_PER_ROOM: int = 2
MAX_PLAYERS_PER_ROOM: int = 4

# How long to wait before auto-starting a partially filled room (seconds)
MATCHMAKING_FILL_TIMEOUT: float = 10.0

# =============================================================================
# Match timer
# =============================================================================

MATCH_DURATION: int = 180  # seconds

# =============================================================================
# Snake defaults
# =============================================================================

SNAKE_INITIAL_LENGTH: int = 10
SNAKE_BASE_SPEED: float = 120.0  # units per second
SNAKE_TURN_RATE: float = 200.0   # degrees per second (smooth turning)
SNAKE_SEGMENT_SPACING: float = 8.0  # pixels between segments

# =============================================================================
# Food
# =============================================================================

TARGET_FOOD_COUNT: int = 200
FOOD_RADIUS: float = 5.0
FOOD_SCORE_VALUE: int = 10
FOOD_LENGTH_GAIN: int = 1

# How many food items to spawn per dead snake segment
DEATH_FOOD_RATIO: float = 0.5

# =============================================================================
# Collision
# =============================================================================

SNAKE_HEAD_RADIUS: float = 8.0
SNAKE_BODY_RADIUS: float = 6.0

# =============================================================================
# Networking
# =============================================================================

WEBSOCKET_HOST: str = "0.0.0.0"
WEBSOCKET_PORT: int = 8765
MAX_MESSAGE_SIZE: int = 2 ** 20  # 1 MiB

# =============================================================================
# Rate Limiting
# =============================================================================

RATE_LIMIT_WINDOW: float = 1.0  # seconds
RATE_LIMIT_MAX_MESSAGES: int = 60  # per window

# =============================================================================
# Match Start Countdown
# =============================================================================

MATCH_START_COUNTDOWN: float = 3.0  # seconds between MATCH_FOUND and MATCH_START
