# py_mono/tools/tool_loader.py
"""
Dynamic tool loader for py-coding-agent.

Scans the dynamic_tools/ folder for Python files and loads any Tool instances
found in them into the agent's tool registry at runtime.

Tools are identified by type (isinstance check against Tool), not by name,
so any exported variable of type Tool will be loaded regardless of its name.

Callers (py_mono/main.py, py_mono/agent/agent.py) are expected to gate calls
to load_dynamic_tools() behind ENABLE_DYNAMIC_TOOLS — see py_mono/config.py —
since dynamic tools are LLM-generated code that executes on load (ISS-003).
This module additionally runs a static, non-executing safety check (the same
forbidden-pattern scan skills already use) on every file before exec_module,
as defense-in-depth independent of that gate.
"""

import ast
import importlib.util
import pathlib
from py_mono.skill.validator import check_forbidden_patterns
from py_mono.tools.tool import Tool


def _static_check(code: str) -> list:
    """Non-executing safety check: syntax validity + forbidden patterns.
    Returns a list of problem strings; empty means the file passed."""
    problems = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        problems.append(f"SyntaxError at line {e.lineno}: {e.msg}")
        return problems  # can't meaningfully scan patterns in unparseable code
    problems.extend(check_forbidden_patterns(code))
    return problems


def load_dynamic_tools(folder: str = "dynamic_tools") -> list:
    """
    Load all dynamic tools from the specified folder.

    Scans all .py files in the folder, statically checks each for known-unsafe
    patterns and syntax validity (without executing it), imports files that
    pass as a module, and collects any attributes that are instances of Tool.
    Skips files that fail the static check or fail to import, logging a
    warning instead of crashing.

    Args:
        folder (str): Path to the dynamic tools folder (default: 'dynamic_tools')

    Returns:
        list: List of Tool instances found across all files in the folder
    """
    tools = []
    path = pathlib.Path(folder)

    if not path.exists():
        return tools

    for file in path.glob("*.py"):
        try:
            code = file.read_text(encoding="utf-8")
            problems = _static_check(code)
            if problems:
                print(f"⚠️ Skipping dynamic tool {file.name} — failed safety check: {'; '.join(problems)}")
                continue

            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr in vars(module).values():
                if isinstance(attr, Tool):
                    tools.append(attr)
        except Exception as e:
            print(f"⚠️ Failed to load dynamic tool {file.name}: {e}")

    return tools