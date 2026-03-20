from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path
from pathlib import Path

def list_files(path=".", recursive=False, max_depth=2):
    """
    List files in the workspace directory.

    Args:
        path (str): Relative path inside workspace
        recursive (bool): Whether to list files recursively
        max_depth (int): Maximum recursion depth
    """
    base_path = resolve_safe_path(path)

    if not base_path.exists():
        return f"[ERROR] Path does not exist: {path}"

    def walk(dir_path: Path, depth: int):
        if depth > max_depth:
            return []

        entries = []
        for item in sorted(dir_path.iterdir()):
            if item.is_dir():
                entries.append({
                    "type": "dir",
                    "name": item.name,
                    "children": walk(item, depth + 1) if recursive else []
                })
            else:
                entries.append({
                    "type": "file",
                    "name": item.name
                })
        return entries

    tree = walk(base_path, depth=0)

    return str(tree)   


list_files_tool = Tool(
    name="list_files",
    description="List files and directories in the workspace",
    func=list_files,
    parameters={
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Relative path inside workspace (default: current directory)"
            },
            "recursive": {
                "type": "boolean",
                "description": "Whether to recursively list files"
            },
            "max_depth": {
                "type": "integer",
                "description": "Maximum recursion depth (default: 2)"
            }
        },
        "required": []
    }
)
