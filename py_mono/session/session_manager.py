# py_mono/session/session_manager.py

from typing import Optional

from py_mono.llm.base import LLMProvider
from py_mono.llm.provider_registry import get_provider


class SessionManager:
    """
    Manages per-session provider state and supports temporary overrides.

    This first pass uses env‑based keys only; KeyManager integration can be
    added later without breaking this interface.
    """

    def __init__(self, default_provider: str = "ollama", model: Optional[str] = None):
        self.provider_name: str = default_provider
        self.provider: LLMProvider = get_provider(default_provider, model=model)
        self._override_provider: Optional[LLMProvider] = None

    def switch_provider(self, name: str, model: Optional[str] = None) -> None:
        """
        Permanently switch provider for this session.
        """
        self.provider_name = name
        self.provider = get_provider(name, model=model)

    def use_provider_once(self, name: str, model: Optional[str] = None) -> None:
        """
        Temporarily override provider for one request only.
        """
        self._override_provider = get_provider(name, model=model)

    def get_active_provider(self) -> LLMProvider:
        """
        Return the effective provider for this request.
        Consumes any temporary override.
        """
        if self._override_provider is not None:
            p = self._override_provider
            self._override_provider = None
            return p
        return self.provider
