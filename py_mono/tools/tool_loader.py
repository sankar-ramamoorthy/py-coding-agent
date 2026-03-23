# py_mono/tools/tool_loader.py
"""
Dynamic tool loader for py-coding-agent.

Scans the dynamic_tools/ folder for Python files and loads any Tool instances
found in them into the agent's tool registry at runtime.

Tools are identified by type (isinstance check against Tool), not by name,
so any exported variable of type Tool will be loaded regardless of its name.
"""

import importlib.util
import pathlib
from py_mono.tools.tool import Tool


def load_dynamic_tools(folder: str = "dynamic_tools") -> list:
    """
    Load all dynamic tools from the specified folder.

    Scans all .py files in the folder, imports each as a module, and collects
    any attributes that are instances of Tool. Skips files that fail to import
    and logs a warning instead of crashing.

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
            spec = importlib.util.spec_from_file_location(file.stem, file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            for attr in vars(module).values():
                if isinstance(attr, Tool):
                    tools.append(attr)
        except Exception as e:
            print(f"⚠️ Failed to load dynamic tool {file.name}: {e}")

    return tools