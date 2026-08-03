**Architectural Decision Record (ADR)** focused specifically on **safety and sandboxing** for the Python coding agent with dynamic tools. 

---

# ADR 001: Safe Execution of Tools in Python Coding Agent

**Status:** Accepted
**Date:** 2026-03-21
**Corrected:** 2026-08-03 — the original claims below were contradicted by the actual code
(see `docs/project-audit-2026-08-02.md` finding C-02, tracked as `ISS-002`). This document
has been corrected to describe the real, now-fixed behavior. See
`specs/003-fix-workspace-sandbox/` for the implementing feature.

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

   * All file paths in tools must be resolved using `resolve_safe_path(path)`, which checks real path containment (`Path.is_relative_to()` against the resolved workspace root) rather than a textual prefix comparison — a sibling directory whose name happens to share the workspace root's text is correctly rejected, as is `../` traversal and a symlink inside the workspace that resolves outside it.
   * An operator may explicitly configure `ADDITIONAL_ALLOWED_PATHS` (empty by default) to grant additional directories the same accessibility as the workspace, as a deliberate, on-purpose decision — not as an accidental side effect of a bug.
   * Any attempt to access a path outside the workspace and outside every configured additional directory raises a `ValueError`; this propagates to the caller as an exception (not a caught, returned string) — corrected from this ADR's original, inaccurate claim.
   * Dynamic tools must follow the same rule; the agent enforces this when creating the template for new tools.

2. **LLM-friendly Output**

   * Tools must return strings summarizing results or errors.
   * Avoid returning raw exceptions or large binary outputs.
   * This ensures the LLM can reason over outputs and avoid guessing or hallucinating.

3. **Shell Command Restrictions**

   * The shell tool is **disabled by default** and only becomes available when an operator explicitly sets `ENABLE_SHELL_TOOL=true` — this is the only way it becomes available.
   * Shell commands are filtered for forbidden patterns (`rm -rf /`, `shutdown`, `reboot`) and a subprocess timeout (30s) now applies. This is **defense-in-depth only, not a security boundary**: `cwd=/workspace` does not restrict what an arbitrary shell command can read, write, or reach — a command like `cat /etc/passwd` is not blocked, corrected from this ADR's original implication that `cwd` provided meaningful containment.
   * Enabling the shell tool does not, by itself, narrow or widen its reach — only whether it is available at all changes. True containment of shell command *content* would require OS-level isolation (a separate restricted container, chroot, seccomp), which is intentionally out of scope here — see `specs/003-fix-workspace-sandbox/`.

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

   * File tools cannot access paths outside `/workspace` (or an explicitly configured additional allowed directory) — enforced by real path containment.
   * The shell tool, when an operator has explicitly enabled it, is **not** privilege-restricted — the forbidden-pattern blocklist catches a few known-risky commands (e.g. `sudo`), not all privilege-escalation paths. This is a known, accepted limitation of the opt-in shell capability, not a claim of full containment.

---

## Consequences

* **Safety:** File tool operations are sandboxed to `/workspace` plus any explicitly configured additional directories. The shell tool, when enabled, is not content-sandboxed — this is a conscious, documented trade-off, not an oversight.
* **LLM Reliability:** Clear, string-based outputs help the LLM reason over results without hallucinating.
* **Dynamic Flexibility:** LLM can create new tools on the fly safely.
* **Limitations:** File tools are constrained to the workspace plus configured additional directories. The development container's mount of the project source is read-only at runtime — only the workspace, dynamic-tools, and skills directories remain writable. Some desired operations outside these areas may require special approval or an admin tool.

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
