# py_mono/config.py
"""
Configuration for py-coding-agent.

Environment Variables:

LLM Provider:
    LLM_PROVIDER        — 'ollama-auto' (default), 'ollama-remote', 'ollama-local',
                          'ollama' (legacy single-backend), or 'litellm'

Ollama (legacy single-backend, used only when LLM_PROVIDER=ollama):
    OLLAMA_BASE_URL     — base URL for Ollama host (default: http://host.docker.internal:11434)
    OLLAMA_MODEL        — model name (default: lfm2.5-thinking:latest)

Ollama dual-backend (used by ollama-auto/ollama-remote/ollama-local):
    OLLAMA_REMOTE_URL   — remote (GPU) Ollama base URL (default: http://100.105.24.12:11434)
    OLLAMA_REMOTE_MODEL — remote default model (default: qwen3.5:4b)
    OLLAMA_LOCAL_URL    — local Ollama base URL (default: http://host.docker.internal:11434)
    OLLAMA_LOCAL_MODEL  — local default model (default: Qwen3:4b)

LiteLLM (optional, set LLM_PROVIDER=litellm):
    LITELLM_MODEL       — model string in litellm format (default: groq/llama-3.3-70b-versatile)
    GROQ_API_KEY        — if using Groq
    OPENAI_API_KEY      — if using OpenAI
    ANTHROPIC_API_KEY   — if using Anthropic

Workspace:
    WORKSPACE_ROOT           — path to sandboxed workspace (default: /workspace)
    ADDITIONAL_ALLOWED_PATHS — comma-separated list of extra directories, beyond
                               WORKSPACE_ROOT, that file tools may access. Empty by
                               default — nothing beyond the workspace is accessible
                               until explicitly configured here.

Shell tool:
    ENABLE_SHELL_TOOL   — 'true'/'1'/'yes'/'on' to enable the shell tool (default: false,
                          disabled). The shell tool is NOT a content sandbox — enabling it
                          grants the agent shell command execution with the same reach it
                          has always had (filtered only by a best-effort blocklist, not
                          confined to the workspace). Only enable in a trusted environment.
"""

import os
from pathlib import Path

# LLM provider selection
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama-auto")

# Ollama settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "lfm2.5-thinking:latest")

# LiteLLM settings
LITELLM_MODEL = os.getenv("LITELLM_MODEL", "groq/llama-3.3-70b-versatile")



WORKSPACE_ROOT = Path(os.getenv("WORKSPACE_ROOT", "/workspace")).resolve()

_additional_paths_raw = os.getenv("ADDITIONAL_ALLOWED_PATHS", "")
ADDITIONAL_ALLOWED_PATHS = [
    Path(p.strip()).resolve() for p in _additional_paths_raw.split(",") if p.strip()
]

# Shell tool gating
ENABLE_SHELL_TOOL = os.getenv("ENABLE_SHELL_TOOL", "false").strip().lower() in (
    "1", "true", "yes", "on",
)
