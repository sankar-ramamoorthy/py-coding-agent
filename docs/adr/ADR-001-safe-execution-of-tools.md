**Architectural Decision Record (ADR)** focused specifically on **safety and sandboxing** for the Python coding agent with dynamic tools. 

---

# ADR 001: Safe Execution of Tools in Python Coding Agent

**Status:** Proposed
**Date:** 2026-03-21

## Context

The Python coding agent is designed to execute arbitrary tasks by calling tools. Tools can be:

* Built-in: `read_file`, `write_file`, `list_files`, `shell`, etc.
* Dynamic: User-requested tools created at runtime via `create_tool`.

Because tools can access the filesystem and execute code, there is a **risk of unsafe operations**, including:

* Accessing files outside the intended workspace.
* Executing destructive shell commands.
* Reading sensitive system files.
* Infinite loops or excessive recursion.

Dynamic tools are especially risky because they are generated at runtime based on LLM instructions, which may not always be safe or correct.

---

## Decision

1. **Workspace Sandboxing**

   * All file paths in tools must be resolved using `resolve_safe_path(path)` which ensures paths remain inside the `/workspace` root directory.
   * Any attempt to access files outside `/workspace` will return an error string, not raise an exception.
   * Dynamic tools must follow the same rule; the agent enforces this when creating the template for new tools.

2. **LLM-friendly Output**

   * Tools must return strings summarizing results or errors.
   * Avoid returning raw exceptions or large binary outputs.
   * This ensures the LLM can reason over outputs and avoid guessing or hallucinating.

3. **Shell Command Restrictions**

   * Shell commands are filtered for forbidden patterns (`rm -rf /`, `shutdown`, `reboot`).
   * Commands execute with `cwd=/workspace` to prevent accidental system-wide effects.

4. **Dynamic Tool Creation**

   * The `create_tool` tool is used to write Python code into `dynamic_tools/`.
   * After creation, the agent immediately loads the new tool using `load_dynamic_tools()` and updates its tool registry.
   * The LLM is nudged to generate tools **following the safe template**, which enforces:

     * Use of `resolve_safe_path()` for file paths.
     * Return values that are clear, concise strings.
     * Defined `Tool` metadata (name, description, parameters).

5. **Agent-level Guardrails**

   * Loop detection: Repeated tool calls with identical arguments trigger a system nudging message to the LLM.
   * Max steps per query prevent runaway loops.

6. **No elevated privileges**

   * The agent cannot access files outside `/workspace`.
   * The agent cannot execute commands that require admin/root privileges.

---

## Consequences

* **Safety:** All tool operations are sandboxed to `/workspace`.
* **LLM Reliability:** Clear, string-based outputs help the LLM reason over results without hallucinating.
* **Dynamic Flexibility:** LLM can create new tools on the fly safely.
* **Limitations:** Tools are constrained to `/workspace`. Some desired operations outside the workspace may require special approval or an admin tool.

---

## Example Safe Template for Dynamic Tools

```
from py_mono.tools.tool import Tool
from py_mono.utils.path_utils import resolve_safe_path

def my_dynamic_tool(path, content):
    safe_path = resolve_safe_path(path)
    with open(safe_path, "a", encoding="utf-8") as f:
        f.write(content)
    return f"Appended {len(content)} characters to {safe_path}"

my_dynamic_tool_tool = Tool(
    "my_dynamic_tool",
    "Append content to a file safely inside workspace",
    my_dynamic_tool,
    parameters={
        "type": "object",
        "properties": {
            "path": {"type": "string"},
            "content": {"type": "string"}
        },
        "required": ["path", "content"]
    }
)
```

---

This ADR makes it clear to the team that **dynamic tool creation cannot bypass the sandbox or safety rules**, while maintaining the minimal pi-mono agent loop.

---
