# py_mono/llm/base.py
"""
Abstract base class for LLM providers.

All providers must implement:
- generate(): send messages to the LLM and return a normalized response
- to_wire_messages(): translate canonical OpenAI-style memory to provider wire format

See ADR-005 for the canonical message format specification.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Base class for all LLM providers."""

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