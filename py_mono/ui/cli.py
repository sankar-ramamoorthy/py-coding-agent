# py_mono/ui/cli.py

"""
Command-line interface for py-coding-agent.

Handles:
- /key groq <api_key>      → store encrypted key
- /key list                → list providers with keys
- /key remove <provider>   → remove a stored key
- everything else          → passed to agent
"""

from typing import Optional

from py_mono.security.key_manager import KeyManager
from py_mono.session.session_manager import SessionManager
from py_mono.agent.agent import Agent
from py_mono.config import WORKSPACE_ROOT
import os


def start_cli(agent: Agent) -> None:
    """
    Start the interactive CLI loop for the coding agent.

    Reads user input, checks for /key commands, then passes everything else
    to the agent.

    Args:
        agent (Agent): Initialized Agent instance to handle user queries
    """
    print("Welcome to Python Coding Agent (V1)!")
    print("Type 'exit' or 'quit' to quit.")
    print("Type '/clear' to reset memory, '/bye' to end session.")
    print("Type '/key help' for key management help.\n")

    while True:
        try:
            prompt = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Goodbye!")
            break

        if not prompt:
            continue

        if prompt.lower() in ("exit", "quit"):
            break

        # Handle /key commands before sending to agent
        if _is_key_command(prompt):
            response = _handle_key_command(prompt, agent.session_manager)
            if response is not None:
                print(response)
        else:
            response = agent.run(prompt)
            if response is not None:
                print(response)


# --- Key-command helpers ---

def _is_key_command(text: str) -> bool:
    """True if the text is a /key command."""
    text = text.strip()
    return text.startswith("/key")


def _handle_key_command(
    text: str,
    session_manager: Optional[SessionManager],
) -> Optional[str]:
    key_manager: Optional[KeyManager] = (
        session_manager._key_manager if session_manager else None
    )

    if not key_manager:
        return "[KEY ERROR] KeyManager not initialized (LLM_MASTER_KEY not set)."

    parts = text.strip().split()
    if len(parts) < 2:
        return (
            "Usage: /key <command> ...\n"
            "Commands: help, groq <key>, openai <key>, list, remove <provider>"
        )

    cmd = parts[1].lower()

    if cmd == "help":
        return (
            "Key management (ADR‑006):\n"
            "/key <provider> <api_key>  → store encrypted key\n"
            "/key list                   → list providers with keys\n"
            "/key remove <provider>     → remove a stored key"
        )

    if cmd in ["groq", "openai", "anthropic"]:  # example providers
        if len(parts) != 3:
            return f"Usage: /key {cmd} <api_key>"
        provider = cmd
        key = parts[2].strip()
        if not key:
            return "API key cannot be empty."
        try:
            key_manager.set(provider, key)
            return f"✅ Stored encrypted key for {provider}."
        except Exception as e:
            return f"[KEY ERROR] {str(e)}"

    if cmd == "list":
        providers = key_manager.list_providers()
        if not providers:
            return "No stored keys."
        return "Providers with keys: " + ", ".join(providers)

    if cmd == "remove" and len(parts) == 3:
        provider = parts[2]
        if key_manager.remove(provider):
            return f"✅ Removed key for {provider}."
        return f"Provider '{provider}' has no stored key."

    return f"Unknown /key command: {cmd}. Try '/key help'."
