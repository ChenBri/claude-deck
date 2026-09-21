from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional

from deck.state import Deck, SessionState


@dataclass
class Context:
    """Everything a scene needs to draw one frame."""

    now: float
    dt: float
    deck: Deck
    session: Optional[SessionState]
    tool_name: str = ""
    tool_target: str = ""  # already sanitized upstream by the daemon
    tool_rate: float = 0.0  # tool calls/sec, drives WORKING animation speed
    idle_info: dict = field(default_factory=dict)  # clock, date, name, weather, git, totals
    inputs: dict = field(default_factory=dict)  # latest joystick/mech-key state for games


class Scene(ABC):
    def on_enter(self, ctx: Context) -> None:
        pass

    def on_exit(self, ctx: Context) -> None:
        pass

    @abstractmethod
    def draw(self, canvas, ctx: Context) -> None:
        ...
