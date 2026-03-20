from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path

def edit_file(path, instructions):
    safe_path = resolve_safe_path(path)

    with open(safe_path, "r", encoding="utf-8") as f:
        content = f.read()

    content += f"\n# Edit instructions:\n{instructions}"

    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Edited {safe_path}"


edit_tool = Tool(
    "edit_file",
    "Edit a file by appending instructions",
    edit_file
)