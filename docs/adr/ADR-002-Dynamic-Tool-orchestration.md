 **dynamic tool orchestration** and how the agent integrates `create_tool` into its pi-mono style loop.

---

# ADR 002: Dynamic Tool Orchestration in Python Coding Agent

**Status:** Proposed
**Date:** 2026-03-21

## Context

The Python coding agent can extend its capabilities **at runtime** via dynamic tools. Dynamic tools are:

* Python scripts written into `dynamic_tools/` by the `create_tool` tool.
* Immediately loadable into the agent’s tool registry using `load_dynamic_tools()`.
* Callable by the agent in the same way as built-in tools.

Dynamic tools enable the LLM to expand functionality beyond pre-defined tools. However, orchestration must ensure:

* Safety constraints are always enforced (see ADR 001).
* The LLM knows when to call `create_tool`.
* The agent updates its tool registry **without restarting**.

---

## Decision

1. **Detecting Intent to Create a Tool**

   * The agent does **not** hardcode knowledge of tool creation in the system prompt.
   * When the LLM issues a `tool_call` to `create_tool`, the agent:

     1. Extracts the `name` and `code` arguments.
     2. Ensures the generated code follows the **safe dynamic tool template** (sandboxed, LLM-friendly output).
     3. Writes the code to `dynamic_tools/{name}.py`.

2. **Loading Dynamic Tools**

   * Immediately after creating the tool, the agent calls `load_dynamic_tools(folder="dynamic_tools")`.

   * Newly created tools are added to `self.tools` dictionary:

     ```python
     for t in load_dynamic_tools("dynamic_tools"):
         self.tools[t.name] = t
     ```

   * This allows the LLM to use the new tool in **the same conversation loop** without restarting the agent.

3. **LLM Prompt Guidance for Tool Creation**

   * The LLM can be nudged via user instructions to generate safe tools, e.g.:

     ```
     Please create a Python tool called safe_append_file:
     - Must use resolve_safe_path for all file paths
     - Must return clear string indicating success or error
     - Must define parameters in Tool metadata
     ```

   * The agent treats this as a normal `tool_call`, so the loop logic remains minimal (pi-mono style).

4. **Orchestration in the Agent Loop**

   * The agent’s loop remains **unchanged** except for:

     * After executing `create_tool`, reload dynamic tools.
     * Record the tool creation result in memory for the LLM.
     * Continue the loop so the LLM can immediately use the new tool.

   * No forced finalization or multi-step reasoning is required — pi-mono minimal loop is preserved.

5. **Safety & Sandboxing Enforcement**

   * All dynamic tools must use `resolve_safe_path`.
   * Tools are confined to `/workspace`.
   * The agent prevents repeated or infinite tool calls via the loop guard (`repeat_count`).

---

## Consequences

* **Dynamic Expansion:** The agent can acquire new capabilities at runtime.
* **Minimal Orchestration:** No need for complex system prompts or multi-step planning.
* **LLM Trust:** The LLM can focus on which tool to call without worrying about the mechanics of tool registration.
* **Safety Preserved:** Dynamic tools are sandboxed and LLM-friendly, maintaining ADR 001 guarantees.

---

### Example Flow

```text
User: "Create a tool to safely append content to a file."
  |
Agent appends user message to memory
  |
LLM generates tool_call("create_tool", {name: "safe_append_file", code: "<template code>"})
  |
Agent executes create_tool → writes dynamic_tools/safe_append_file.py
  |
Agent reloads dynamic tools → self.tools["safe_append_file"] available
  |
Agent records result in memory → LLM can now call safe_append_file()
  |
Loop continues → LLM can call new tool or return final answer
```

---

This ADR complements ADR 001 (safety) and explains **how dynamic tools fit into the pi-mono minimal loop** without complicating prompts.

---

