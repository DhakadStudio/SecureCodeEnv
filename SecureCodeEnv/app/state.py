"""
SecureCodeEnv - Episode State
Manages per-session state during an RL episode.
"""
from dataclasses import dataclass, field
from typing import Optional
from codegraph.graph import CodeGraph


@dataclass
class EpisodeState:
    task: dict
    graph: CodeGraph
    step: int = 0
    done: bool = False
    scores_history: list = field(default_factory=list)
    created_at: float = field(default_factory=lambda: __import__('time').time())

    def is_expired(self, ttl_seconds: int = 3600) -> bool:
        """Sessions expire after 1 hour to prevent memory leaks."""
        return (__import__('time').time() - self.created_at) > ttl_seconds
