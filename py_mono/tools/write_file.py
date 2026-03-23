# py_mono/tools/write_file.py
from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path
from pathlib import Path

def write_file(path=None, content=""):
    """
    Write content to a file.

    Args:
        path (str): Relative path inside workspace (default: './output.txt')
        content (str): Content to write

    Returns:
        str: Success message or actionable error
    """
    # default path if empty or '.'
    if not path or path.strip() == ".":
        path = "./output.txt"

    safe_path = resolve_safe_path(path)

    try:
        # ensure parent directories exist
        safe_path.parent.mkdir(parents=True, exist_ok=True)
        
        # write content
        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(content)

        return f"✅ File written successfully: {safe_path}"

    except Exception as e:
        return f"[TOOL ERROR] Could not write file {path}: {str(e)}"


write_tool = Tool(
    name="write_file",
    description="Write content to a file. Defaults to './output.txt' if path is empty or '.'",
    func=write_file,
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path inside workspace (default: './output.txt')"
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file"
            }
        },
        "required": ["content"]
    }
)