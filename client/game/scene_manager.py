"""
Scene Manager — Manages scene lifecycle and transitions.

Only one scene is active at a time.  The SceneManager delegates
event handling, updating, and rendering to the active scene.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from game.game_app import GameApp


class Scene(ABC):
    """
    Abstract base class for all game scenes.

    Each scene represents a distinct screen (menu, matchmaking, gameplay, etc.).
    Scenes are created by the SceneManager and receive a reference to the
    GameApp for accessing shared resources (network client, renderer, etc.).
    """

    def __init__(self, app: "GameApp") -> None:
        self.app: "GameApp" = app

    @abstractmethod
    def enter(self) -> None:
        """Called when this scene becomes the active scene."""
        ...

    @abstractmethod
    def exit(self) -> None:
        """Called when this scene is being replaced by another."""
        ...

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Process a single Pygame event."""
        ...

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance the scene logic by *dt* seconds."""
        ...

    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """Draw the scene onto the screen surface."""
        ...


class SceneManager:
    """
    Manages scene instances and transitions.

    Usage:
        manager = SceneManager(app)
        manager.register("menu", MenuScene)
        manager.switch("menu")
    """

    def __init__(self, app: "GameApp") -> None:
        self._app: "GameApp" = app
        self._scenes: dict[str, type[Scene]] = {}
        self._active: Scene | None = None
        self._active_name: str = ""

    @property
    def active_scene(self) -> Scene | None:
        """The currently active scene instance."""
        return self._active

    @property
    def active_name(self) -> str:
        """Name key of the active scene."""
        return self._active_name

    def register(self, name: str, scene_class: type[Scene]) -> None:
        """Register a scene class under a name key."""
        self._scenes[name] = scene_class

    def switch(self, name: str, **kwargs: Any) -> None:
        """
        Switch to a different scene.

        The current scene's `exit()` is called, then the new scene
        is instantiated and its `enter()` is called.
        """
        if name not in self._scenes:
            raise ValueError(f"Unknown scene: {name!r}")

        # Exit current scene
        if self._active is not None:
            self._active.exit()

        # Create and enter new scene
        scene_class = self._scenes[name]
        self._active = scene_class(self._app)
        self._active_name = name
        self._active.enter()

    def handle_event(self, event: pygame.event.Event) -> None:
        """Forward event to the active scene."""
        if self._active:
            self._active.handle_event(event)

    def update(self, dt: float) -> None:
        """Forward update to the active scene."""
        if self._active:
            self._active.update(dt)

    def render(self, screen: pygame.Surface) -> None:
        """Forward render to the active scene."""
        if self._active:
            self._active.render(screen)
