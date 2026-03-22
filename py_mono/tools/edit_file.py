# py_mono/tools/edit_file.py
from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path
from pathlib import Path

def edit_file(path=None, instructions=""):
    """
    Edit a file by appending instructions.

    Args:
        path (str): Relative path inside workspace (default: './output.txt')
        instructions (str): Text to append to the file

    Returns:
        str: Success message or actionable error
    """
    # default path if empty or '.'
    if not path or path.strip() == ".":
        path = "./output.txt"

    safe_path = resolve_safe_path(path)

    if not safe_path.exists():
        return f"[TOOL ERROR] File not found: {path}. Use write_file() to create it first."

    if safe_path.is_dir():
        return f"[TOOL ERROR] Path is a directory: {path}. Use list_files() to see directory contents."

    try:
        # read current content
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()

        # append instructions safely
        content += f"\n# Edit instructions:\n{instructions}"

        # write back
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"✅ Edited file successfully: {safe_path}"

    except Exception as e:
        return f"[TOOL ERROR] Could not edit file {path}: {str(e)}"


edit_tool = Tool(
    name="edit_file",
    description="Edit a file by appending instructions. Defaults to './output.txt' if path is empty or '.'",
    func=edit_file,
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path inside workspace (default: './output.txt')"
            },
            "instructions": {
                "type": "string",
                "description": "Text to append to the file"
            }
        },
        "required": ["instructions"]
    }
)