import ast
import inspect
import pathlib
import re

from py_mono.skill.validator import check_forbidden_patterns
from py_mono.tools.tool import Tool

TOOLS_DIR = pathlib.Path("dynamic_tools")
VALID_TOOL_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def create_tool(name, code):
    if not VALID_TOOL_NAME.fullmatch(name):
        return "Error: tool name must be a valid Python identifier."

    try:
        TOOLS_DIR.mkdir(parents=True, exist_ok=True)
        path = (TOOLS_DIR / f"{name}.py").resolve()

        # detect function
        match = re.search(r"def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\((.*?)\)", code)
        if not match:
            return "Error: no function found."

        func_name = match.group(1)
        args = match.group(2)

        # 🔥 build parameter schema
        params = [a.strip().split("=")[0] for a in args.split(",") if a.strip()]
        properties = {
            p: {"type": "string"} for p in params
        }

        required = params

        wrapped_code = f"""
from py_mono.tools.tool import Tool

{code}

{name}_tool = Tool(
    name="{name}",
    description="Auto-generated tool: {name}",
    func={func_name},
    parameters={{
        "type": "object",
        "properties": {properties},
        "required": {required},
    }},
)
"""

        # Static safety check on the exact content that will be written and
        # later executed — refuse to persist anything containing a known-
        # unsafe pattern or that fails to parse (ISS-003).
        try:
            ast.parse(wrapped_code)
        except SyntaxError as e:
            return f"Error: generated tool code has a syntax error at line {e.lineno}: {e.msg}"

        forbidden = check_forbidden_patterns(wrapped_code)
        if forbidden:
            return "Error: generated tool code failed the safety check: " + "; ".join(forbidden)

        path.write_text(wrapped_code, encoding="utf-8")

        return f"✅ Tool '{name}' created with schema: {path}"

    except Exception as exc:
        return f"Error creating tool {name}: {exc}"


create_tool_tool = Tool(
    "create_tool",
    "Create a new Python tool dynamically",
    create_tool,
    parameters={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Python module name for the tool file to create.",
            },
            "code": {
                "type": "string",
                "description": "Full Python source code for the tool module.",
            },
        },
        "required": ["name", "code"],
    },
)