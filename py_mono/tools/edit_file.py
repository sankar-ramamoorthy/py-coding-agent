from py_mono.tools.tool import Tool

def edit_file(path, instructions):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    content += f"\n# Edit instructions:\n{instructions}"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"Edited {path}"

edit_tool = Tool(
    "edit_file",
    "Edit a file by appending instructions",
    edit_file
)