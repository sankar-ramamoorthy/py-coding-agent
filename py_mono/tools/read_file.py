# py_mono/tools/read_file.py
from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path
from pathlib import Path

def read_file(path="."):
    """
    Read the content of a file.

    Args:
        path (str): Relative path inside workspace (default: current directory)

    Returns:
        str: File contents, or actionable error message
    """
    # default to current directory if path is empty or '.'
    if not path or path.strip() == ".":
        path = "."

    safe_path = resolve_safe_path(path)

    if not safe_path.exists():
        return f"[TOOL ERROR] File not found: {path}. Use '.' for current directory."

    if safe_path.is_dir():
        return f"[TOOL ERROR] Path is a directory: {path}. Use list_files() to see directory contents."

    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"[TOOL ERROR] Could not read file {path}: {str(e)}"


read_tool = Tool(
    name="read_file",
    description="Read the contents of a file. Defaults to '.' for current directory.",
    func=read_file,
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path inside workspace (default: current directory)"
            }
        },
        "required": []
    }
)