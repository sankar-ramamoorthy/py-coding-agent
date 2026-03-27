# py_mono/llm/provider_registry.py

from typing import Dict, Type

from py_mono.llm.base import LLMProvider
from py_mono.llm.ollama_provider import OllamaProvider
from py_mono.llm.litellm_provider import LiteLLMProvider
from typing import Optional


REGISTRY: Dict[str, Type[LLMProvider]] = {
    "ollama": OllamaProvider,
    "litellm": LiteLLMProvider,
    # If you later want finer‑grained names like "groq", "openai", etc.,
    # you can still map them to LiteLLMProvider with a model hint.
}


def get_provider(name: str, model: Optional[str] = None) -> LLMProvider:
    """
    Simple factory: return an LLMProvider instance for a given name.

    For now:
    - OllamaProvider uses OLLAMA_MODEL, OLLAMA_BASE_URL
    - LiteLLMProvider uses LITELLM_MODEL, API_KEYs from env.

    Key management (encrypted /key commands) will plug into this later.
    """
    cls = REGISTRY.get(name)
    if not cls:
        raise ValueError(
            f"Unknown provider: {name}. Available: {list(REGISTRY.keys())}"
        )
    return cls(model_name=model)  # tight‑bound model
