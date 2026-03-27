# py_mono/llm/base.py

from abc import ABC, abstractmethod
from typing import Optional


class LLMProvider(ABC):
    """Base class for all LLM providers."""

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name
        # providers can override or interpret this as needed

    @abstractmethod
    def generate(self, messages: list, tools: list = None) -> dict:
        """
        Send messages to the LLM and return a normalized response.

        Args:
            messages: Canonical OpenAI-style message list
            tools: List of Tool objects

        Returns:
            {"text": str | None, "tool_call": {"name": str, "args": dict} | None}
        """
        pass

    @abstractmethod
    def to_wire_messages(self, messages: list) -> list:
        """
        Translate canonical OpenAI-style messages to provider wire format.

        Args:
            messages: Canonical OpenAI-style message list

        Returns:
            list: Provider-specific message list ready to send
        """
        pass
