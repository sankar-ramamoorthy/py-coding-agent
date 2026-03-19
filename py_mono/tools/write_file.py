from py_mono.tools.tool import Tool

def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Wrote {len(content)} characters to {path}"

write_tool = Tool(
    "write_file",
    "Write content to a file",
    write_file
)