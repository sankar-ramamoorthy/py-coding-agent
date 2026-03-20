from py_mono.tools.tool import Tool

from py_mono.utils.path_utils import resolve_safe_path

def read_file(path):
    safe_path = resolve_safe_path(path)

    with open(safe_path, "r", encoding="utf-8") as f:
        return f.read()


read_tool = Tool(
    "read_file",
    "Read the contents of a file",
    read_file
)