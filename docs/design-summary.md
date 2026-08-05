# py-coding-agent — Design Summary

`py-coding-agent` is a Dockerized Python-based coding agent that uses an LLM to reason, call
tools, and execute tasks inside a **sandboxed workspace** (`/workspace`).

_Rewritten 2026-08-05 as a single current-state document — see "Document history" at the
bottom for why the previous version needed this instead of another patch._

## Current state (Milestone 5 shipped)

- **Core agent loop** follows a **pi-mono style minimal loop**, using canonical OpenAI-style
  messages, now driven by a **structured orchestration envelope** (ADR-017): the LLM responds
  with either plain text or `{"_type": "agent_action", "action": "answer"|"use_skill", ...}`,
  and the runtime dispatches accordingly rather than only reacting to a typed `/skill` command.
- **Provider-agnostic LLM design** via `LLMProvider`, `OllamaProvider`, and `LiteLLMProvider`
  (ADR-005), with runtime provider switching and tight-bound model selection:
  `/provider <name> [model]` (ADR-009), overriding env defaults for that session, no restart.
- **Docker-based runtime** with a workspace sandbox (`/workspace`), volume-mounted
  `dynamic_tools/`, and an MCP server (`datetime-mcp`) on a shared Docker network.
- **Dependency management** with `uv` and a hybrid lock strategy (ADR-007): local `uv lock` for
  day-to-day work, container-resolved locks before releases or major merges.
- **Provider registry and session management** (ADR-006): `provider_registry.py` maps provider
  names to classes; `SessionManager` holds per-session provider state; `Agent` depends on
  `SessionManager`, not a fixed `llm` instance.
- **Strict tool interface (ADR-014):** `Tool.run(**kwargs)` is the only sanctioned call path;
  direct `.func(...)` access is forbidden, because LLMs kept mis-calling the old form.
- **Skills layer, fully built out** (ADR-010, ADR-012, ADR-013, ADR-014, ADR-015, ADR-016):
  see below.
- **Spec Kit adopted for this repo's own development (ADR-019):** `/speckit-specify` →
  `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`, artifacts in
  `specs/<NNN>-<slug>/`. Distinct from the skills layer's own approval gate and from ADR-018's
  end-user-facing requirements workflow (see below) — three different things that all involve
  the word "spec."

## Providers & LLM integration

- Multi-provider support via LiteLLM (Groq, OpenAI, Anthropic) plus local Ollama (default).
- Runtime provider switching and model binding (`/provider <name> [model]`).
- Session management with memory pruning and tool-aware context.
- Encrypted API key storage (`LLM_MASTER_KEY`).
- Ollama-specific hardening (`ISS-009`): `think: false` by default plus `num_predict`/`num_ctx`
  as a safety net, so a thinking-capable local model can't silently exhaust its response budget
  on internal reasoning and return empty content.

## Tools

- Built-in: `list_files`, `read_file`, `write_file`, `edit_file`, `shell`,
  `install_dependency`, `create_tool`.
- Dynamic tools created at runtime via `create_tool.py`; must be registered to be discoverable.
- Tools are called internally from skills for modular workflows, always via `Tool.run(...)`.

## Skills layer

Structured, reusable workflows, invocable either via `/skill <name> ...` or by the LLM's own
`action: "use_skill"` choice (ADR-017).

### Design

- `skills/<skill_name>/SKILL.md` — Markdown spec + YAML front-matter (required).
- `skills/<skill_name>/skill.py` — Python implementation (optional).
- `SkillRegistry` discovers skills at startup and tracks `status: proposed` / `status:
  approved`, verified against a hash ledger (`skills/.approvals.json`) so approval can't be
  silently bypassed (`ISS-003`, fixed).
- `SkillContext` provides `workspace_root`, `session_manager`, and `agent_tools` to every skill
  at runtime.
- Skills can call existing tools, write and run tests, and read/write code in the sandbox — but
  never touch the filesystem or shell directly (ADR-016).

### Current skills (9)

- `bug_fix` — fix bugs from stack traces or error messages.
- `refactor_extract_function` — extract code blocks into helper functions.
- `doc_sync` — keep doc comments and READMEs in sync with code.
- `hello` — example skill demonstrating the interactive generator workflow.
- `generate_skill` — interactive in-repo skill scaffolder (`/skill generate_skill`); new skills
  default to `status: proposed`.
- `create_skill_py` — scaffolds `skill.py` for a skill that only has a `SKILL.md` so far.
- `generate_playbook` — mirrors `generate_skill`'s pattern for the reasoning layer.
- `scaffold_project` — requirements-driven project scaffolding for end users (ADR-018): reads
  `workspace/requirements.md`, generates a file manifest, writes files via `write_file`, runs
  `pytest` if tests were generated.
- `listallpy` — lists Python files in the workspace.

### CLI commands

```text
/skill list                    → list all skills
/skill help <skill_name>       → show skill spec (SKILL.md)
/skill <skill_name> ...        → run an approved skill
/skill generate_skill ...      → scaffold a new skill (dev-only)
```

## Skills vs tools

| Aspect         | Skill                        | Tool                                     |
| -------------- | ----------------------------- | ----------------------------------------- |
| Discovery      | Dynamic via `SkillRegistry`   | Manual registration via `create_tool.py` |
| Execution      | Local Python + helpers        | Single Python function, local execution  |
| Invocation     | `/skill ...` or LLM `use_skill` action | Called from within skills or the agent loop |
| Complexity     | Multi-step workflows          | Usually single-purpose utility           |
| Scaffold       | `/skill generate_skill`       | Manual creation or `create_tool.py`      |

Skills are higher-level, approval-gated workflows; tools are lower-level utilities they call
into.

## Roadmap

Not duplicated here — see `docs/ROADMAP_PLAN.md` for current milestone sequencing (Milestone 6
reliability foundation, Milestone 7 skill lifecycle graph, Milestone 8 provenance/sharing, and
what's explicitly gated pending the personal-tool-vs-multi-user decision). Keeping the future
list in one place instead of copied here is deliberate — this file drifted out of sync with
reality before precisely because it carried its own separate future-work list.

## Summary

The agent supports a fully-featured skills layer — deterministic, multi-step, approval-gated
workflows — combined with tools, providers, session management, and sandboxed execution. The
approval gate (`proposed → approved → runnable`) is this project's most differentiated asset: a
governance story (capabilities a human signs off on), not just a capability story (an agent
that writes and runs code).

## Document history

This file previously carried a "Milestone 2 → 3" pass followed by a full second document
nested inside a Markdown code fence labeled "Milestone 5 update," left mid-edit with an
unclosed fence. That structure is gone as of this rewrite; if you need the pre-2026-08-05
content, it's in git history for this file, not preserved inline.
