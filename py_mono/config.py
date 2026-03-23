# py_mono/config.py
"""
Configuration for py-coding-agent.

Environment Variables:

LLM Provider:
    LLM_PROVIDER        — 'ollama' (default) or 'litellm'

Ollama (default):
    OLLAMA_BASE_URL     — base URL for Ollama host (default: http://host.docker.internal:11434)
    OLLAMA_MODEL        — model name (default: lfm2.5-thinking:latest)

LiteLLM (optional, set LLM_PROVIDER=litellm):
    LITELLM_MODEL       — model string in litellm format (default: groq/llama-3.3-70b-versatile)
    GROQ_API_KEY        — if using Groq
    OPENAI_API_KEY      — if using OpenAI
    ANTHROPIC_API_KEY   — if using Anthropic

Workspace:
    WORKSPACE_ROOT      — path to sandboxed workspace (default: /workspace)
"""

import os
from pathlib import Path

# LLM provider selection
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "lfm2.5-thinking:latest")

# LiteLLM settings
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "groq/llama-3.3-70b-versatile")



WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "/workspace")).resolve()
