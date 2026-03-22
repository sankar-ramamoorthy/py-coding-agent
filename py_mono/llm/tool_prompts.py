# py_mono/llm/tool_prompts.py

def build_create_tool_prompt(tool_name: str, description: str, parameters: dict, instructions: str = "") -> str:
    """
    Build a prompt for the LLM to generate a safe, LLM-friendly dynamic tool.
    
    Args:
        tool_name: Name of the tool to create
        description: Short description of the tool's purpose
        parameters: Dict of parameters in standard Tool format
        instructions: Optional extra instructions for the tool logic
    Returns:
        str: Full prompt text
    """
    param_lines = []
    for param, meta in parameters.get("properties", {}).items():
        param_lines.append(f"- {param} ({meta.get('type', 'any')}): {meta.get('description', '')}")
    param_text = "\n".join(param_lines)

    return f"""
You are a Python coding agent. Your task is to generate a dynamic Python tool file.

Tool name: {tool_name}
Description: {description}

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
{instructions}

Please output **only valid Python code** that defines the tool.
"""