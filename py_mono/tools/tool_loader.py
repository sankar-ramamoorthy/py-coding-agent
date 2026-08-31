# py_mono/tools/tool_loader.py
"""
Dynamic tool loader for py-coding-agent.

Scans the dynamic_tools/ folder for Python files, statically extracts Tool
metadata, and returns worker-backed Tool proxies.

Callers (py_mono/main.py, py_mono/agent/agent.py) are expected to gate calls
to load_dynamic_tools() behind ENABLE_DYNAMIC_TOOLS — see py_mono/config.py —
since dynamic tools are LLM-generated code that executes on load (ISS-003).
This module additionally runs a static, non-executing safety check (the same
forbidden-pattern scan skills already use) on every file before exposing a
worker-backed proxy, as defense-in-depth independent of that gate.
"""

import ast
import pathlib
from dataclasses import dataclass
from typing import Any, Optional

from py_mono.skill.validator import check_forbidden_patterns
from py_mono.tools.tool import Tool
from py_mono.tools.worker import run_dynamic_tool_in_worker


@dataclass
class DynamicToolMetadata:
    name: str
    description: str
    parameters: dict[str, Any]


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


def _extract_tool_metadata(code: str) -> Optional[DynamicToolMetadata]:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "Tool":
            continue

        values = {keyword.arg: keyword.value for keyword in node.keywords if keyword.arg}
        name_node = values.get("name") or (node.args[0] if len(node.args) >= 1 else None)
        description_node = values.get("description") or (
            node.args[1] if len(node.args) >= 2 else None
        )
        parameters_node = values.get("parameters") or (
            node.args[3] if len(node.args) >= 4 else None
        )
        if name_node is None or description_node is None:
            continue
        try:
            name = ast.literal_eval(name_node)
            description = ast.literal_eval(description_node)
            parameters = (
                ast.literal_eval(parameters_node)
                if parameters_node is not None
                else {"type": "object", "properties": {}, "required": []}
            )
        except (ValueError, SyntaxError):
            continue
        if isinstance(name, str) and isinstance(description, str) and isinstance(parameters, dict):
            return DynamicToolMetadata(name=name, description=description, parameters=parameters)
    return None


def _build_worker_tool(file: pathlib.Path, metadata: DynamicToolMetadata) -> Tool:
    def run_in_worker(**kwargs):
        return run_dynamic_tool_in_worker(
            module_path=file,
            tool_name=metadata.name,
            args=kwargs,
        )

    return Tool(
        name=metadata.name,
        description=metadata.description,
        func=run_in_worker,
        parameters=metadata.parameters,
    )


def load_dynamic_tools(folder: str = "dynamic_tools") -> list:
    """
    Load all dynamic tools from the specified folder.

    Scans all .py files in the folder, statically checks each for known-unsafe
    patterns and syntax validity (without executing it), extracts Tool metadata
    from files that pass, and returns worker-backed proxies. Skips files that
    fail the static check or metadata extraction, logging a warning instead of
    crashing.

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

            metadata = _extract_tool_metadata(code)
            if metadata is None:
                print(f"Skipping dynamic tool {file.name} - no static Tool metadata found")
                continue
            tools.append(_build_worker_tool(file, metadata))
        except Exception as e:
            print(f"⚠️ Failed to load dynamic tool {file.name}: {e}")

    return tools
