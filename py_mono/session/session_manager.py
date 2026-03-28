# py_mono/session/session_manager.py  (fixed)

from typing import Optional
import os

from py_mono.llm.base import LLMProvider
from py_mono.llm.provider_registry import get_provider
from py_mono.security.key_manager import KeyManager


class SessionManager:
    """
    Manages per-session provider state and supports temporary overrides.
    Also integrates KeyManager for runtime API key management.
    """

    def __init__(
        self,
        default_provider: str = "ollama",
        model: Optional[str] = None,
        key_manager: Optional[KeyManager] = None,
    ):
        # Initialize key_manager first
        self._key_manager: Optional[KeyManager] = key_manager

        self.provider_name: str = default_provider
        self.provider: LLMProvider = self._resolve_provider(default_provider, model)
        self._override_provider: Optional[LLMProvider] = None

    def switch_provider(self, name: str, model: Optional[str] = None) -> None:
        """
        Permanently switch provider for this session.
        Optionally bind a model for this provider instance.
        """
        self.provider_name = name
        self.provider = self._resolve_provider(name, model)

    def use_provider_once(self, name: str, model: Optional[str] = None) -> None:
        """
        Temporarily override provider for one request only.
        """
        self._override_provider = self._resolve_provider(name, model)

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

    def _resolve_key(self, provider: str) -> Optional[str]:
        """
        Resolve an API key for a provider:

        1. Session-level key (stored encrypted via /key)
        2. Environment variable fallback
        3. None
        """
        if self._key_manager is not None and self._key_manager.has(provider):
            return self._key_manager.get(provider)

        # Env fallback: try reasonable key env vars
        env_key_vars = {
            "litellm": [
                "GROQ_API_KEY",
                "OPENAI_API_KEY",
                "ANTHROPIC_API_KEY",
            ],
        }
        for key_env in env_key_vars.get(provider, []):
            val = os.getenv(key_env)
            if val:
                return val

        return None

    def _resolve_provider(self, name: str, model: Optional[str] = None) -> LLMProvider:
        """
        Build provider, resolving API key via KeyManager or env.
        """
        api_key = self._resolve_key(name) if self._key_manager is not None else None
        return get_provider(name=name, model=model, api_key=api_key)
