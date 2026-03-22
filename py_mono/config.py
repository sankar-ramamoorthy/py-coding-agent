"""
Configuration for py-coding-agent.

Environment Variables:
- LLM_PROVIDER: Name of the LLM provider to use (default: 'ollama')
- OLLAMA_BASE_URL: Base URL to reach the Ollama host from inside Docker
- OLLAMA_MODEL: Ollama model to use
"""

import os
from pathlib import Path

DEFAULT_LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "lfm2.5-thinking:latest")



WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "/workspace")).resolve()
