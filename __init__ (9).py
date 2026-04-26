from __future__ import annotations

from collections import deque
from dataclasses import dataclass


@dataclass
class Turn:
    user: str
    assistant: str
    tag: str
    confidence: float


class ConversationMemory:
    def __init__(self, max_turns: int = 10) -> None:
        self.max_turns = max_turns
        self.turns: deque[Turn] = deque(maxlen=max_turns)

    def add(self, user: str, assistant: str, tag: str, confidence: float) -> None:
        self.turns.append(Turn(user=user, assistant=assistant, tag=tag, confidence=confidence))

    def last_tag(self) -> str | None:
        if not self.turns:
            return None
        return self.turns[-1].tag

    def context_text(self) -> str:
        if not self.turns:
            return ""
        parts = [f"U:{t.user} A:{t.assistant}" for t in self.turns]
        return " || ".join(parts)
