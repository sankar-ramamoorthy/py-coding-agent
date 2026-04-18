# py_mono/llm/tool_prompts.py

"""
Prompt builders for future LLM-assisted tool and skill generation flows.

This module is intentionally kept even though it is not part of the current
runtime path. Today, dynamic tools are exposed through registered `Tool`
objects and provider tool schemas, so `create_tool` does not call these
helpers directly.

Retaining this module documents the intended prompt shape for a future
implementation where the agent may ask an LLM to scaffold tool code before
writing it into `dynamic_tools/`.
"""

from typing import Dict


def _escape_for_fstring(s: str) -> str:
    """
    Escape braces and double quotes for safe interpolation into prompt text.
    """
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("{", "{{").replace("}", "}}")
    s = s.replace('"', '\\"')
    return s


def build_create_tool_prompt(
    tool_name: str,
    description: str,
    parameters: Dict,
    instructions: str = "",
) -> str:
    """
    Build a prompt for a future LLM-driven tool scaffolding step.

    This helper is currently unused at runtime. Keep it aligned with the
    `Tool` contract so it remains a valid starting point if that flow is added.
    """
    safe_tool_name = _escape_for_fstring(tool_name)
    safe_description = _escape_for_fstring(description)
    safe_instructions = _escape_for_fstring(instructions)

    param_lines = []
    for param, meta in parameters.get("properties", {}).items():
        type_ = meta.get("type", "any")
        desc = meta.get("description", "")
        param_lines.append(f"- {param} ({type_}): {desc}")
    param_text = "\n".join(param_lines) or "- None"

    prompt = f"""
You are a Python coding agent. Your task is to generate a dynamic Python tool file.

Tool name: {safe_tool_name}
Description: {safe_description}

Parameters:
{param_text}

Requirements for the tool code:
- All file operations must use `resolve_safe_path` to stay inside /workspace.
- Tool should return a clear string indicating success or errors.
- Do not raise unhandled exceptions; return errors in string format.
- Tool must define a `Tool` object with correct `name`, `description`, `func`, and `parameters`.
- Keep the code minimal and LLM-friendly.
- The tool should NOT require external dependencies beyond standard library.

Extra instructions (optional):
{safe_instructions}

Please output only valid Python code that defines the tool.
"""

    return prompt.strip()
