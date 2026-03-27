# Py-Coding-Agent Design Document

## Goal

Build a local Python coding agent inspired by **pi-mono** that can:

- Execute tasks safely in a **sandbox** (`/workspace`)
- Dynamically create, load, and run Python tools
- Install Python packages as needed
- Interface with local or cloud LLMs via a provider abstraction layer

---

## Architecture Overview

The agent uses a **minimal loop**, letting the LLM decide whether to call a tool or return a final answer. Tools can be **built-in** or **dynamically created** at runtime. The LLM provider is abstracted so the agent works with Ollama locally or any cloud provider via LiteLLM.

```
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
```

**Dynamic Tool Lifecycle:**

```
LLM calls create_tool
   │
   ▼
Agent executes create_tool(code) → writes to dynamic_tools/
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
  * Volume mounted — no rebuild required for new tools
* **Python packages** installed via `uv`
* **LLM** via Ollama (local default) or LiteLLM (cloud providers)

---

## LLM Provider Abstraction (ADR-005)

The agent maintains a **canonical OpenAI-style message format** internally.
Each provider translates to/from its own wire format in its own class.
The agent never knows what provider it is talking to.

```
agent.py  →  canonical memory format
                    │
                    ▼
         OllamaProvider    → translates to Ollama wire format
         LiteLLMProvider   → pass-through (OpenAI native)
                                   │
                                   ├── groq/qwen/qwen3-32b
                                   ├── openai/gpt-4o
                                   └── anthropic/claude-3-5-haiku
```

Provider selected via `LLM_PROVIDER` environment variable:
- `ollama` — default, direct HTTP, no extra dependencies
- `litellm` — cloud providers, requires `LITELLM_MODEL` and API key

---

## Minimal Loop Behavior (pi-mono style)

* Agent appends user input to memory
* LLM decides on each step:
  * Call a tool (with arguments)
  * Return final answer
* Agent executes tool, records result in memory
* Result fed back to LLM for next iteration
* Loop continues until LLM outputs final answer
* Loop has **repeat-detection guard** to prevent infinite tool calls
* Memory **auto-pruned** every N tool calls (default: 5), keeping last 20 messages

---

## Tools

### Built-in

* `list_files` — List files and directories (supports recursion)
* `read_file` — Read file contents
* `write_file` — Write content to files
* `edit_file` — Find-and-replace editing (read file first for exact content)
* `shell` — Execute shell commands (restricted to `/workspace`)
* `install_dependency` — Install Python packages via `uv`
* `create_tool` — Dynamically create new Python tools

### Dynamic Tools

* Created at runtime via `create_tool`
* Must follow sandbox rules (`resolve_safe_path`)
* Discovered via `isinstance(attr, Tool)` scan — no hardcoded attribute name
* Immediately available after `load_dynamic_tools()`
* Volume mounted — persist across container restarts

---

## Memory & Session Management

The agent maintains a **conversation memory**:

1. **System prompt** — immutable, always preserved
2. **User messages**
3. **Assistant tool calls** (canonical format)
4. **Tool results**
5. **Assistant text responses**

**Special Commands**

- `/clear` → resets conversation memory to system prompt only, resets all loop guards
- `/bye` → terminates session

**Auto-Pruning**

- Prunes memory automatically after `auto_prune_after` tool calls (default 5)
- Keeps last `prune_keep_last` messages (default 20)
- System prompt always preserved

---

## V1 Scope (Milestone 1 ✅)

* CLI‑driven agent
* Base toolset with safe file + shell operations
* Minimal agent loop (pi‑mono style)
* Dynamic tool creation and runtime loading
* Workspace sandbox enforcement
* LLM integration via Ollama

## V2 Scope (Milestone 2 ✅)

* Multi‑provider LLM support via LiteLLM (ADR‑005)
* Docker Compose with volume mounts
* Config‑driven environment
* MCP Server (ADR‑004)

## V3 Implemented (Milestone 3)

* Provider registry pattern (ADR‑006)
* Session manager with per‑session provider state
* Runtime provider switching (e.g. `/provider ollama`, `/provider litellm`)
* Tight‑binding model selection in provider instances (ADR‑009)
* **Dependency locking strategy (ADR‑007)** — hybrid `uv lock` workflow on host vs Docker

## V3 Planned / In‑progress

* Encrypted API key management via KeyManager
* Smart provider routing by task type (ADR‑008) — e.g., `ollama` for local/private, `groq` for fast tools, `anthropic` for complex reasoning

## V4 Ideas

* Multi-agent pods: planner, coder, tester
* Tool schema validation and registry
* Memory indexing for tools
* Automatic tool testing
* Offload older memory to disk/DB

---

## Key Principles

* **Safety First** — All operations restricted to `/workspace`
* **Minimal Loop** — LLM controls flow, agent just orchestrates
* **Dynamic Extensibility** — New tools can be created and loaded at runtime
* **Provider Agnostic** — Agent never knows what LLM it is talking to
* **Transparency** — Tool results fed back to LLM, agent logs each step