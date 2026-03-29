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
