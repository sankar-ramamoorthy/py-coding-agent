from py_mono.tools.tool import Tool
import pathlib

TOOLS_DIR = pathlib.Path("dynamic_tools")

def create_tool(name, code):
    path = TOOLS_DIR / f"{name}.py"

    with open(path, "w") as f:
        f.write(code)

    return f"Tool {name} created at {path}"

create_tool_tool = Tool(
    "create_tool",
    "Create a new Python tool dynamically",
    create_tool
)