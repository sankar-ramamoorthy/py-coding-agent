# py_mono/llm/provider_registry.py

import os
from typing import Dict, Type

from py_mono.llm.base import LLMProvider
from py_mono.llm.ollama_provider import OllamaProvider
from py_mono.llm.litellm_provider import LiteLLMProvider
from py_mono.llm.ollama_connectivity import is_ollama_reachable
from typing import Optional


REGISTRY: Dict[str, Type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "ollama-remote": OllamaProvider,
    "ollama-local": OllamaProvider,
    "ollama-auto": OllamaProvider,
    "litellm": LiteLLMProvider,
    # If you later want finer‑grained names like "groq", "openai", etc.,
    # you can still map them to LiteLLMProvider with a model hint.
}

# Explicit named Ollama backends. "ollama" (bare) is deliberately NOT here — it keeps
# its original meaning, reading only OLLAMA_BASE_URL/OLLAMA_MODEL directly inside
# OllamaProvider, so it stays byte-for-byte backward compatible.
_OLLAMA_BACKENDS = {
    "ollama-remote": {
        "base_url_env": "OLLAMA_REMOTE_URL",
        "base_url_default": "http://100.105.24.12:11434",
        "model_env": "OLLAMA_REMOTE_MODEL",
        "model_default": "qwen3.5:4b",
    },
    "ollama-local": {
        "base_url_env": "OLLAMA_LOCAL_URL",
        "base_url_default": "http://host.docker.internal:11434",
        "model_env": "OLLAMA_LOCAL_MODEL",
        "model_default": "Qwen3:4b",
    },
}


def get_provider(
    name: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
) -> LLMProvider:
    """
    Simple factory: return an LLMProvider instance for a given name  and optional key.
.

    For now:
    - OllamaProvider uses OLLAMA_MODEL, OLLAMA_BASE_URL (unused: api_key).
    - "ollama-remote"/"ollama-local" resolve base_url/model from their own env vars
      (see _OLLAMA_BACKENDS) and never probe or fall back — a failure is a real,
      direct connection error.
    - "ollama-auto" probes ollama-remote's reachability once (short timeout) and
      resolves to ollama-remote if reachable, else ollama-local.
    - LiteLLMProvider uses LITELLM_MODEL, and API key from api_key first, then env.

    Key management (encrypted /key commands) plugs into this via api_key.

    """
    cls = REGISTRY.get(name)
    if not cls:
        raise ValueError(
            f"Unknown provider: {name}. Available: {list(REGISTRY.keys())}"
        )

    if name == "ollama-auto":
        remote = _OLLAMA_BACKENDS["ollama-remote"]
        remote_url = os.getenv(remote["base_url_env"], remote["base_url_default"])
        name = "ollama-remote" if is_ollama_reachable(remote_url) else "ollama-local"
        cls = REGISTRY[name]

    if name in _OLLAMA_BACKENDS:
        backend = _OLLAMA_BACKENDS[name]
        base_url = os.getenv(backend["base_url_env"], backend["base_url_default"])
        resolved_model = model or os.getenv(backend["model_env"], backend["model_default"])
        return cls(model_name=resolved_model, api_key=api_key, base_url=base_url)

    return cls(model_name=model, api_key=api_key) # tight‑bound model
