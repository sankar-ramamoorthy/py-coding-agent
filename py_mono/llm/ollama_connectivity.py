# py_mono/llm/ollama_connectivity.py

import requests


def is_ollama_reachable(base_url: str, timeout: float = 2.0) -> bool:
    """
    Best-effort reachability check for an Ollama backend.

    Runs once at provider-resolution time (e.g. when "ollama-auto" is selected),
    never per-request. A short timeout is enough to distinguish an unreachable
    backend from one that's merely slow to answer /api/tags.
    """
    try:
        resp = requests.get(f"{base_url}/api/tags", timeout=timeout)
        return resp.ok
    except requests.RequestException:
        return False
