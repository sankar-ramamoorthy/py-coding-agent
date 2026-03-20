from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path

def write_file(path, content):
    safe_path = resolve_safe_path(path)

    safe_path.parent.mkdir(parents=True, exist_ok=True)

    with open(safe_path, "w", encoding="utf-8") as f:
        f.write(content)

    return f"Wrote {len(content)} characters to {safe_path}"


write_tool = Tool(
    "write_file",
    "Write content to a file",
    write_file
)