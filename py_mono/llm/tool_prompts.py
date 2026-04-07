# py_mono/llm/tool_prompts.py

"""
Safe prompt builders for LLM-powered dynamic tools and skill generation.

Escapes curly braces and quotes in user-supplied input to avoid
Python string formatting errors (like 'Invalid format specifier').
"""

from typing import Dict

def _escape_for_fstring(s: str) -> str:
    """
    Escape curly braces and double quotes to safely embed in f-strings.
    """
    if not isinstance(s, str):
        s = str(s)
    s = s.replace("{", "{{").replace("}", "}}")   # escape curly braces
    s = s.replace('"', '\\"')                     # escape double quotes
    return s

def build_create_tool_prompt(
    tool_name: str,
    description: str,
    parameters: Dict,
    instructions: str = "",
) -> str:
    """
    Build a prompt for the LLM to generate a safe, LLM-friendly dynamic tool.

    Args:
        tool_name: Name of the tool to create
        description: Short description of the tool's purpose (str, dict, JSON, or list)
        parameters: Dict of parameters in standard Tool format
        instructions: Optional extra instructions for the tool logic

    Returns:
        str: Full prompt text
    """
    # Sanitize inputs
    safe_tool_name = _escape_for_fstring(tool_name)
    safe_description = _escape_for_fstring(description)
    safe_instructions = _escape_for_fstring(instructions)

    # Format parameters safely
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

Please output **only valid Python code** that defines the tool.
"""

    return prompt.strip()