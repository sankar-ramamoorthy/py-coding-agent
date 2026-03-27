# utils/special_commands.py

from typing import Optional, List, Dict

from py_mono.session.session_manager import SessionManager


def is_special_command(text: str) -> bool:
    text = text.strip()
    if text == "/clear":
        return True
    if text == "/bye":
        return True
    if text.startswith("/providers"):
        return True
    if text.startswith("/provider "):
        return True
    return False


def handle_special_command(
    text: str,
    session_manager: SessionManager,
    memory: List[dict],
    guards: Dict[str, int],
) -> Optional[str]:
    text = text.strip()
        if text == "/clear":
        if memory:
            system = memory[0]
            memory.clear()
            memory.append(system)
        guards["tool_repeat_count"] = 0
        guards["tool_repeat_tool"] = None
        return "Cleared conversation history (system prompt preserved)."

    if text == "/bye":
        return "Bye!"

    if text == "/providers":
        active = session_manager.get_active_provider()
        # Assuming `get_provider_names()` exists on your registry or provider
        # You may need to adapt this to your actual registry API.
        # For now, an example placeholder:
        available = ", ".join(sorted(["ollama", "litellm"]))  # or fetch from registry
        return f"Active provider: {active.__class__.__name__}\nAvailable providers: {available}"

    if text.startswith("/provider "):
        parts = text.split(maxsplit=1)
        if len(parts) != 2:
            return "Usage: /provider <provider_name>"
        name = parts[1].strip()
        try:
            session_manager.switch_provider(name)
            current = session_manager.get_active_provider()
            return f"Switched provider to {current.__class__.__name__} ({name})."
        except Exception as e:
            return f"Could not switch provider: {e}"

    return None
