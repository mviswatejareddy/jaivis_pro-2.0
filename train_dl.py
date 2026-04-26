from __future__ import annotations

from dataclasses import dataclass

from .commands import COMMANDS
from .memory import ConversationMemory
from ..ml.predictor import IntentPredictor


@dataclass
class AssistantConfig:
    confidence_threshold: float = 0.45
    memory_turns: int = 10
    address_user_as: str = "Boss"


class JarvisAssistant:
    def __init__(self, config: AssistantConfig | None = None) -> None:
        self.config = config or AssistantConfig()
        self.predictor = IntentPredictor()
        self.memory = ConversationMemory(max_turns=self.config.memory_turns)

    def _persona(self, text: str) -> str:
        if not text:
            return text
        low = text.lower()
        if "boss" in low:
            return text
        return f"{text} Boss."

    def handle(self, user_text: str) -> tuple[str, bool]:
        contextual_text = user_text
        last_tag = self.memory.last_tag()
        if last_tag and any(x in user_text.lower() for x in ["and", "also", "then", "what about", "again"]):
            contextual_text = f"{user_text} [last_intent={last_tag}]"

        tag, confidence = self.predictor.predict(contextual_text)
        if confidence < self.config.confidence_threshold:
            tag = "fallback"

        if tag == "exit":
            response = self.predictor.get_response(tag)
            self.memory.add(user_text, response, tag, confidence)
            return self._persona(response), True

        if tag in COMMANDS:
            response = COMMANDS[tag](user_text)
            self.memory.add(user_text, response, tag, confidence)
            return self._persona(response), False

        response = self.predictor.get_response(tag)
        self.memory.add(user_text, response, tag, confidence)
        return self._persona(response), False
