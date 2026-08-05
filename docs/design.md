# Py-Coding-Agent Design Document

_Rewritten 2026-08-05 to fix a broken nested-fence edit and restore two sections
(`Special Commands`, `Auto-Pruning`) that had been displaced from where they belong — see
"Document history" at the bottom. Content is otherwise the same design, brought current._

## Goal

Build a local Python coding agent inspired by **pi-mono** that can:

- Execute tasks safely in a **sandbox** (`/workspace`)
- Dynamically create, load, and run Python tools
- Install Python packages as needed
- Interface with local or cloud LLMs via a provider abstraction layer

---

## Architecture Overview

The agent uses a **minimal loop**, letting the LLM decide whether to call a tool or return a
final answer. Tools can be **built-in** or **dynamically created** at runtime. The LLM provider
is abstracted so the agent works with Ollama locally or any cloud provider via LiteLLM. As of
ADR-017, the LLM's decision is a structured `agent_action` JSON envelope
(`action: "answer" | "use_skill"`), not just implicit tool calls — see
`docs/architectural-diagram.md` for the full current flow; the diagram below is the original,
simpler mental model and still holds for the tool-call path.

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
  * (ADR-017) Emit a structured `agent_action` envelope selecting `answer` or `use_skill`
* Agent executes tool or skill, records result in memory
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

### Tool execution interface (ADR-014)

All tool execution MUST go through `Tool.run(**kwargs)`, never `tool.func(...)` or `_func`
directly — introduced after LLMs repeatedly mis-called the old direct-function form
(positional args, dict-as-positional args). `Tool.run` is the enforcement point for any future
argument validation, logging, or retries.

---

## Skills Layer (ADR-010, ADR-012, ADR-013, ADR-014, ADR-015, ADR-016)

A skills layer sits on top of the minimal loop and tools, exposing higher-level workflows via
`/skill <name> ...` — or, since ADR-017, via the LLM's own `action: "use_skill"` choice.

### Design

- Each skill is defined under:
  - `skills/<skill_name>/SKILL.md` (required)
  - `skills/<skill_name>/skill.py` (optional subclass of `Skill`)
- `SkillRegistry`:
  - Discovers all `skills/<skill_name>/SKILL.md` files
  - Loads `skill.py` if present
  - Tracks `status: proposed` / `status: approved` for each skill, verified against a hash
    ledger (`skills/.approvals.json`) so approval can't be bypassed (`ISS-003`, fixed)
- `SkillContext`:
  - Provides `workspace_root`, `session_manager`, and `agent_tools` to every skill at runtime
- Skills can:
  - Call existing tools (`read_file`, `write_file`, `shell`, etc.) — always via `Tool.run(...)`
  - Write tests and run them
  - Read and write code in the sandbox

### Safety and approval model (ADR-010)

- By default, skills are `status: proposed` and **not executable**.
- Only when `status: approved` may an agent run the skill.
- This mimics a PR-style review gate: "spec + code exists, but must be explicitly approved
  before execution."

### Dual-layer architecture and enforcement (ADR-015, ADR-016)

Skills (execution) are deliberately kept separate from playbooks (reasoning):

- **Reasoning layer** — `playbooks/`, Markdown-only, interpreted by the LLM, never executable.
- **Execution layer** — `skills/`, Python-backed, approval-gated, deterministic.
- **Orchestration** — decides which skill to invoke; structured per ADR-017 (see above).

ADR-016 makes this a hard constraint, not just a convention: the LLM must never directly mutate
the workspace; every side effect goes through an approved skill or a tool; playbooks must never
contain executable instructions.

### Example skills

- `bug_fix` — input: error message + file + line range; output: minimal fix + small test.
- `refactor_extract_function` — input: file + start/end line + new function name; output: new
  helper function + updated caller + test.
- `scaffold_project` (ADR-018) — input: `workspace/requirements.md`; output: a generated file
  manifest written via `write_file`, with `pytest` run afterward if tests were generated.

Nine skills exist as of 2026-08-05: `bug_fix`, `refactor_extract_function`, `doc_sync`, `hello`,
`generate_skill`, `create_skill_py`, `generate_playbook`, `scaffold_project`, `listallpy`.

| Aspect                | Claude-style skills                                       | py-coding-agent skills                                       |
| ---------------------- | ----------------------------------------------------------- | -------------------------------------------------------------- |
| Skill definition       | Markdown-driven (SKILL.md / natural-language steps)         | Markdown spec (SKILL.md) plus executable code (skill.py)      |
| Where logic lives      | The LLM "reads the markdown and figures out how to act."    | Explicit Python (`run(...)`, tool calls, tests)                |
| Runtime precision      | Flexible, LLM-interpreted.                                  | Deterministic, code-defined behavior                            |
| Safety / review model  | Often controlled by UI / toggles.                           | Explicit approval gate in YAML (`status: proposed`/`approved`) |

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
- `/provider <name> [model]` → runtime provider/model switch (ADR-009)
- `/skill <name> ...` → run an approved skill

**Auto-Pruning**

- Prunes memory automatically after `auto_prune_after` tool calls (default 5)
- Keeps last `prune_keep_last` messages (default 20)
- System prompt always preserved

---

## Scope by milestone

### V1 Scope (Milestone 1 ✅)

* CLI-driven agent
* Base toolset with safe file + shell operations
* Minimal agent loop (pi-mono style)
* Dynamic tool creation and runtime loading
* Workspace sandbox enforcement
* LLM integration via Ollama

### V2 Scope (Milestone 2 ✅)

* Multi-provider LLM support via LiteLLM (ADR-005)
* Docker Compose with volume mounts
* Config-driven environment
* MCP Server (ADR-004)

### V3 Scope (Milestone 3 ✅)

* Provider registry pattern (ADR-006)
* Session manager with per-session provider state
* Runtime provider switching (e.g. `/provider ollama`, `/provider litellm`)
* Tight-binding model selection in provider instances (ADR-009)
* Dependency locking strategy (ADR-007) — hybrid `uv lock` workflow on host vs Docker
* Encrypted API key management via KeyManager

### V4 — Skills-layer groundwork (Milestone 5, folded into V5 below)

* Smart provider routing by task type (ADR-008) — proposed, not yet implemented; see
  `docs/ROADMAP_PLAN.md` for its current status (evidence-backed candidate, not filed as
  `ISS-NNN` yet)

### V5 Scope (Milestone 5 ✅)

* Agent skills layer: reusable workflows via `/skill <name>` (ADR-010, ADR-012, ADR-013,
  ADR-014)
* Reference skills: `bug_fix`, `refactor_extract_function`, `doc_sync`, `hello`
* Execution gating: `status: proposed` / `status: approved`
* Interactive in-repo skill generator (`/skill generate_skill`)

### V6 Scope (post-Milestone-5, implemented since — through ADR-019)

* Interactive skill scaffolding refined (ADR-011); `create_skill_py`, `generate_playbook`,
  `scaffold_project`, `listallpy` skills added
* Skills-vs-tools terminology clarified (ADR-012)
* Skill approval and chaining policy (ADR-013): approved skills may chain only to other
  approved skills
* Strict tool execution interface, `Tool.run(**kwargs)` (ADR-014)
* Dual-layer skill architecture: reasoning (playbooks) vs. execution (skills) vs. orchestration
  (ADR-015)
* Boundary enforcement between the three layers made a hard constraint (ADR-016)
* Structured orchestration interface: LLM emits `{"action": "answer"|"use_skill", ...}` JSON,
  implemented in `py_mono/agent/agent.py` / `py_mono/llm/prompts.py` (ADR-017) — note the ADR's
  own header still says `Status: Proposed`; the code is ahead of the ADR's paperwork
* Project scaffold and requirements-driven workflow for end users: `requirements.md`,
  `software-design` playbook, `scaffold_project`, `understand-workspace` skills (ADR-018)
* Spec-Driven Development adopted for this repo's own contributor workflow via GitHub Spec Kit,
  `specs/<NNN>-<slug>/` (ADR-019) — distinct from ADR-018's end-user-facing product feature

### What's next

Not duplicated here — see `docs/ROADMAP_PLAN.md` for current milestone sequencing (Milestone 6
reliability foundation, Milestone 7 skill lifecycle graph, Milestone 8 provenance/sharing) and
`docs/ISSUES.md` for the live issue register. This file previously carried its own separate
"V5 Ideas" future-work wishlist (multi-agent pods, tool registry, memory indexing, smarter task
decomposition); those items now live only in `docs/ROADMAP_PLAN.md`'s "Gated / deferred" table
to avoid the two lists drifting apart, which is exactly what had happened here.

---

## Key Principles

* **Safety First** — All operations restricted to `/workspace`
* **Minimal Loop** — LLM controls flow, agent just orchestrates
* **Dynamic Extensibility** — New tools can be created and loaded at runtime
* **Provider Agnostic** — Agent never knows what LLM it is talking to
* **Transparency** — Tool results fed back to LLM, agent logs each step
* **Governance over generated capability** — skills are reviewable (`SKILL.md`) independently of
  their implementation (`skill.py`), and nothing runs until a human explicitly approves it

---

## Document history

This file previously had a "Skills Layer (Milestone 5)" section pasted in via a mismatched
Markdown code fence (opened with ` ```markdown `, closed with a bare ` ``` ` several sections
later), which pushed the "Special Commands" and "Auto-Pruning" content — originally meant to
sit directly under "Memory & Session Management" — out to after the broken fence instead. Both
issues are fixed in this rewrite: the fence is gone, and those two sections are back where they
belong. If you need the exact prior wording, it's in git history for this file.
