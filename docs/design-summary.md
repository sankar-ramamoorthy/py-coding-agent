# py-coding-agent — Design Summary
# docs\design-summary.md
`py-coding-agent` is a Dockerized Python‑based coding agent that uses an LLM to reason, call tools, and execute tasks inside a **sandboxed workspace** (`/workspace`).

## Current State (Milestone 2 → 3)

- **Core agent loop** follows a **pi‑mono style minimal loop**, using canonical OpenAI‑style messages.  
- **Provider‑agnostic LLM design** via `LLMProvider`, `OllamaProvider`, and `LiteLLMProvider` (ADR‑005).  
- **Docker‑based runtime** with:
  - Workspace sandbox (`/workspace`).  
  - Volume‑mounted `dynamic_tools/`.  
  - MCP server (`datetime‑mcp`) on a shared Docker network.  
- **Dependency management** with `uv` and reproducible `uv.lock` (ADR‑007).  
- **Provider registry and session management** (ADR‑006):
  - `py_mono/llm/provider_registry.py` maps provider names to classes.  
  - `py_mono/session/session_manager.py` holds per‑session provider state and temporary overrides.  
  - `Agent` depends on `SessionManager`, not a fixed `llm` instance.  
- **Runtime provider switching**:
  - CLI commands like `/provider ollama`, `/provider litellm`, and `/providers` are implemented.  
  - `/provider <name> <model>` supports **tight‑binding model selection** (ADR‑009), overriding or complementing env variables.  

## Smart Provider Routing (ADR‑008)

An **ADR‑008‑style smart provider router** is being designed to auto‑select the best LLM for each task type. The idea is to route:

- **Local / private tasks** (e.g. file inspection, shell execution) to a local `ollama` model,  
- **Fast, low‑cost tool calls** (e.g. simple code generation or tool‑use decisions) to cost‑efficient cloud providers like `groq`, and  
- **Complex planning or reasoning‑heavy tasks** (e.g. multi‑step refactoring, architecture design) to higher‑quality models like `anthropic` or `gpt‑4o`.  

The router is envisioned to operate **inside the `SessionManager`**: it takes a canonical request, inspects metadata (tool stack, task complexity, privacy flags), and returns the best `LLMProvider` instance for that step, while keeping the agent’s own logic clean.

## Where It’s Going (Milestone 3)

- **Runtime provider switching**:
  - CLI commands like `/provider groq`, `/provider ollama`, and `/providers` to inspect and change providers at runtime.  
- **Encrypted API key management**:
  - `py_mono/security/key_manager.py` (future) for encrypted on‑disk keys, with `LLM_MASTER_KEY` as an environment‑only secret.  
- **Smart provider routing by task type** (ADR‑008):
  - Heuristic‑based router that picks `ollama` for local/private, `groq` for fast tools, `anthropic` for complex reasoning, etc.  
- **Tight‑binding model selection (ADR‑009)**:
  - Implemented: `/provider <provider> <model>` binds the model to the provider instance, making it truthfully the active model for that session.  
  - Env variables remain the default fallback when no model is explicitly given.


**Agent skills layer (Milestone 5)**:
  - Implement reusable workflows via `/skill <name>`:
    - `bug_fix` — fix bugs from error messages.
    - `refactor_extract_function` — extract blocks into helper functions.
    - `doc_sync` — keep doc comments and READMEs in sync with code.
  - Gate execution with `status: proposed` / `status: approved` (ADR‑010).
  - Allow operator‑approved dry‑run modes for risky skills.

---

#  `design-summary.md` Update (Milestone 5)

````markdown 
# Py-Coding-Agent: Design Summary (Milestone 5)

This update summarizes the current state of the agent and provides a snapshot of implemented features, particularly focusing on the **Skills Layer (Milestone 5)**.

---

## 1. Core Agent Loop

- Multi-step reasoning + execution inspired by pi-mono minimal loop  
- CLI-driven interaction  
- Workspace sandboxing (`/workspace`)  
- File and shell tools (`list_files`, `read_file`, `write_file`, `edit_file`, `shell`)  
- MCP integration for specialized tools (e.g., `datetime-mcp`)  

---

## 2. Providers & LLM Integration

- Multi-provider support via **LiteLLM** (Groq, OpenAI, Anthropic)  
- Local Ollama support (default)  
- Runtime provider switching and model binding (`/provider <name> [model]`)  
- Session management with memory pruning and tool-aware context  
- Encrypted API key storage (`LLM_MASTER_KEY`)  

---

## 3. Tools

- Built-in tools: `list_files`, `read_file`, `write_file`, `edit_file`, `shell`, `install_dependency`, `create_tool`  
- Dynamic tools created at runtime via `create_tool.py`  
- Tools must be registered to be discoverable  
- Tools can be called **internally from skills** for modular workflows  

---

## 4. Skills Layer (Milestone 5)

The **skills layer** provides structured, reusable workflows callable via `/skill <name>`:

### Key Features

- Skills live in `skills/<skill_name>/`  
  - `SKILL.md` — Markdown spec + YAML front-matter  
  - `skill.py` — Python implementation with optional helpers  
- Registered dynamically via `SkillRegistry` at startup  
- Execution gated with `status: proposed / approved` (ADR-010)  
- Skills can call dynamic tools internally, enabling multi-step, deterministic workflows  
- Compatible with lightweight or open-source LLMs, since execution is local  

### Interactive Skill Generator

- Dev-only workflow: `/skill generate-skill` scaffolds a new skill inside the repo  
- Generates `SKILL.md` + `skill.py` with pre-filled helpers and optional tool references  
- New skills are automatically `status: proposed` until reviewed  

### CLI Commands

```text
/skill list                    → list all skills
/skill help <skill_name>       → show skill spec (SKILL.md)
/skill <skill_name> ...        → run an approved skill
/skill generate-skill ...      → scaffold a new skill (dev-only)
````

### Reference Skills

* `bug_fix` — Fix bugs from stack traces or error messages
* `refactor_extract_function` — Extract code blocks into helper functions
* `doc_sync` — Keep doc comments and READMEs in sync with code
* `hello` — Example skill demonstrating the interactive generator workflow

---

## 5. Skills vs Tools

| Aspect         | Skill                        | Tool                                     |
| -------------- | ---------------------------- | ---------------------------------------- |
| Discovery      | Dynamic via SkillRegistry    | Manual registration via `create_tool.py` |
| Execution      | Local Python + helpers       | Single Python function, local execution  |
| LLM Dependency | Optional, reasoning assisted | Optional, only input guidance            |
| Complexity     | Multi-step workflows         | Usually single-purpose utility           |
| Scaffold       | `/skill generate-skill`      | Manual creation or `create_tool.py`      |

Skills are **higher-level workflows**, potentially calling tools for modular execution. Tools remain **lower-level utilities** registered separately.

---

## 6. Milestones

**Milestone 1–4**: Core agent loop, providers, tools, session management, MCP integration ✅

**Milestone 5 (Skills Layer) ✅**

* Reusable workflows via `/skill <name>`
* Reference skills: `bug_fix`, `refactor_extract_function`, `doc_sync`, `hello`
* Execution gating: `status: proposed / approved`
* Developer-approved dry-run modes
* Interactive in-repo skill generator (`/skill generate-skill`)
* Skills can call dynamic tools internally
* Compatible with lightweight/open-source LLMs

---

## 7. Roadmap / Future Enhancements

* Multi-agent system (planner / coder / tester)
* Tool registry with validation and testing
* Memory indexing for tools
* Automated tool testing
* Smarter task decomposition and provider routing
* Additional MCP servers (weather, search, geocoding)
* Packaging and distribution improvements

---

## 8. Summary

The agent now supports **a fully-featured skills layer**, enabling deterministic, multi-step coding workflows. Combined with tools, providers, session management, and sandboxed execution, this design ensures safe, modular, and reproducible agent behavior across LLM providers.

```

---

 This design summary now fully reflects **Milestone 5**:  

- Skills layer  
- Interactive generator  
- Tools called from skills  
- CLI commands updated  
- Lightweight LLM support explicitly mentioned  

---
