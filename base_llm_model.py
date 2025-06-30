# Abstract base class for LLM
from abc import ABC, abstractmethod
from typing import Dict, Optional


class BaseLLMModel(ABC):
    """Abstract base class for LLM implementations."""

    @abstractmethod
    def load(self) -> None:
        """Load the model into memory."""
        pass

    @abstractmethod
    def unload(self) -> None:
        """Unload the model from memory."""
        pass

    @abstractmethod
    def call(self, prompt: str) -> str:
        """Generate a response for a single prompt."""
        pass

    @abstractmethod
    def call_with_messages(self, messages_json: str) -> str:
        """Generate a response for a conversation with multiple messages."""
        pass