````
# Py-Coding-Agent Design Document

## Goal

Build a local Python coding agent inspired by **pi-mono** that can:

- Execute tasks safely in a **sandbox** (`/workspace`)
- Dynamically create, load, and run Python tools
- Install Python packages as needed
- Interface with a local LLM (Ollama)

---

## Architecture Overview

The agent uses a **minimal loop**, letting the LLM decide whether to call a tool or return a final answer. Tools can be **built-in** or **dynamically created** at runtime.

```
ASCII Diagram of Agent Loop (pi-mono style)

User (CLI)
   │
   ▼
Agent Loop
   │
   │ ┌─────────────────────────┐
   │ │ Call LLM for next step  │
   │ └─────────────────────────┘
   │            │
   │            ├───> LLM decides: call a tool
   │            │
   │            ▼
   │       Tool Call
   │            │
   │   ┌─────────────┐
   │   │ Execute Tool │
   │   └─────────────┘
   │            │
   │            ▼
   │       Result returned
   │            │
   │            ▼
   │       Feed back into LLM
   │            │
   │            ▼
   │  LLM decides next step or final answer
   │            │
   └────────────▼
Final Answer → User
````

**Dynamic Tool Lifecycle:**

```
LLM calls `create_tool`
   │
   ▼
build_create_tool_prompt(user_request) → generates Python code
   │
   ▼
Agent executes `create_tool(code)` → writes to dynamic_tools/
   │
   ▼
Agent reloads tools via load_dynamic_tools()
   │
   ▼
Dynamic tool available immediately for use
```

---

## Runtime Environment

* **Docker container** (isolated)
* **Workspace directory (`/workspace`)**

  * All file operations go through `resolve_safe_path()`
  * Prevents access outside sandbox
* **Dynamic tools folder (`dynamic_tools/`)**

  * Runtime-generated Python tools
* **Python packages** installed via `uv`
* **LLM** interface via Ollama (local)

---

## Minimal Loop Behavior (pi-mono style)

* Agent appends user input to memory
* LLM decides on each step:

  * Call a tool (with arguments)
  * Return final answer
* Agent executes tool, records result in memory
* Result fed back to LLM for next iteration
* Loop continues until LLM outputs final answer
* Loop has **simple repeat-detection guard** to prevent infinite tool calls

---

## Tools

### Built-in

* `list_files` — List files and directories (supports recursion)
* `read_file` — Read file contents
* `write_file` — Write content to files
* `edit_file` — Modify files with instructions
* `shell` — Execute shell commands (restricted to `/workspace`)
* `install_dependency` — Install Python packages via `uv`
* `create_tool` — Dynamically create new Python tools

### Dynamic Tools

* Created at runtime via `create_tool`
* Must follow sandbox rules (`resolve_safe_path`)
* Immediately available after `load_dynamic_tools()`
* Can define own parameters via `Tool` metadata

---

---


```markdown
## Memory & Session Management

The agent maintains a **conversation memory**:

1. **System prompt** – immutable
2. **User messages**
3. **Assistant/tool calls**

**Special Commands**

- `/clear` → resets conversation memory
- `/bye` → terminates session

**Auto-Pruning**

- Prunes memory automatically after `auto_prune_after` tool calls (default 5)
- Keeps last `prune_keep_last` messages (default 20)
- Ensures memory does not grow unbounded

## V1 Scope

* CLI-driven agent
* Base toolset with safe file + shell operations
* Minimal agent loop (pi-mono style)
* Dynamic tool creation and runtime loading
* Workspace sandbox enforcement
* LLM integration via Ollama
* MCP Server docs\adr\ADR-004-MCP-Server.md

---

## V2 Ideas

* Multi-agent pods: planner, coder, tester
* Tool schema validation and registry
* Memory indexing for tools
* Automatic tool testing
* Enhanced LLM prompts for tool creation
* More intelligent loop safety and retry logic

* Offload older memory to disk/DB
* Allow configurable pruning policies

---

## Key Principles

* **Safety First** — All operations restricted to `/workspace`
* **Minimal Loop** — LLM controls flow, agent just orchestrates
* **Dynamic Extensibility** — New tools can be created and loaded at runtime
* **Transparency** — Tool results fed back to LLM, agent logs each step

```

---
