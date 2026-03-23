# py_mono/tools/edit_file.py

from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path


def edit_file(path=None, old_content="", new_content=""):
    """
    Edit a file by replacing old_content with new_content.

    The LLM should read the file first to obtain the exact string to replace.
    Only the first occurrence of old_content is replaced.

    Args:
        path (str): Relative path inside workspace (default: './output.txt')
        old_content (str): Exact string to find in the file
        new_content (str): Replacement string

    Returns:
        str: Success message or actionable error
    """
    if not path or path.strip() == ".":
        path = "./output.txt"

    safe_path = resolve_safe_path(path)

    if not safe_path.exists():
        return f"[TOOL ERROR] File not found: {path}. Use write_file() to create it first."

    if safe_path.is_dir():
        return f"[TOOL ERROR] Path is a directory: {path}. Use list_files() to see directory contents."

    if not old_content:
        return "[TOOL ERROR] old_content is required. Read the file first to get the exact string to replace."

    try:
        with open(safe_path, "r", encoding="utf-8") as f:
            content = f.read()

        if old_content not in content:
            return (
                f"[TOOL ERROR] old_content not found in {path}. "
                "Read the file first to get the exact content to replace."
            )

        updated = content.replace(old_content, new_content, 1)

        with open(safe_path, "w", encoding="utf-8") as f:
            f.write(updated)

        return f"✅ Successfully edited {safe_path}"

    except Exception as e:
        return f"[TOOL ERROR] Could not edit file {path}: {str(e)}"


edit_tool = Tool(
    name="edit_file",
    description=(
        "Edit a file by replacing an exact string with new content. "
        "Use read_file() first to get the exact old_content to replace."
    ),
    func=edit_file,
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path inside workspace (default: './output.txt')"
            },
            "old_content": {
                "type": "string",
                "description": "Exact string to find and replace in the file"
            },
            "new_content": {
                "type": "string",
                "description": "Replacement string"
            }
        },
        "required": ["path", "old_content", "new_content"]
    }
)