from py_mono.tools.tool import Tool

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

read_tool = Tool(
    "read_file",
    "Read the contents of a file",
    read_file
)