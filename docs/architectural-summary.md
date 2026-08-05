# Architectural Summary

_Current, actively-maintained version. Supersedes
`docs/architectural-summary-by-codex-20260412.md` (kept, archived, not deleted — see History
below). Update this doc when the architecture actually changes; don't let it go stale for four
months again._

`py-coding-agent` is a Dockerized Python coding agent built around a small core loop, a
sandboxed execution model, and an explicit separation between reasoning, orchestration, and
execution.

## Core loop

User message → LLM responds (plain text, or a structured `agent_action` JSON envelope) →
runtime executes (tool call or skill dispatch) → result returns to the loop. Orchestration is
no longer purely "the LLM decides everything, then the runtime just executes it" — the LLM is
prompted to emit a structured decision (`action: "answer" | "use_skill"`), and the runtime
(`Agent._handle_structured_action`) enforces what happens with that decision, including
skill-approval status. See `docs/architectural-diagram.md` for the full flow.

## Key decisions

- **Sandbox-first execution.** All file access stays inside `/workspace`; tools resolve paths
  safely and avoid unsafe shell patterns. Dynamic tools are hot-loaded but follow the same
  sandbox rules as built-ins.
- **Provider-agnostic LLM layer (ADR-005).** Canonical OpenAI-style messages internally;
  provider-specific translation lives in `OllamaProvider` / `LiteLLMProvider`. `SessionManager`
  plus a provider registry isolate provider switching from agent logic. `/provider <name>
  [model]` tight-binds a model to the session (ADR-009), overriding env defaults without a
  restart — implemented and genuinely live-switchable mid-session.
- **Strict tool interface (ADR-014).** `Tool.run(**kwargs)` is the only sanctioned entry point;
  direct `.func(...)` calls are forbidden. Introduced specifically because LLMs kept mis-calling
  the old direct-function form (positional args, dict-as-positional).
- **Dual-layer skill architecture (ADR-015) plus enforced boundaries (ADR-016).** Three layers:
  reasoning (`playbooks/`, Markdown-only, never executable), orchestration (deciding which skill
  to invoke — now structured per ADR-017, see below), execution (`skills/`, Python-backed,
  approval-gated). The LLM must never touch the filesystem directly; every side effect goes
  through an approved skill or a tool.
- **Structured orchestration interface (ADR-017) — implemented, despite the ADR's own header
  still saying `Status: Proposed`.** `py_mono/llm/prompts.py` prompts the LLM for a
  `{"_type": "agent_action", "action": "answer"|"use_skill", ...}` envelope; `py_mono/agent/
  agent.py` parses and dispatches it. Treat the code as ground truth over the ADR's stale status
  field until someone updates ADR-017 directly.
- **Skill approval gate (ADR-010, ADR-013).** Skills are `status: proposed` until explicitly
  `/approve`d, verified against a hash ledger (`skills/.approvals.json`). This is the project's
  most differentiated feature — a governance story, not just a capability story. A bypass here
  was `ISS-003`, now fixed.
- **Spec-driven development, two flavors that are not the same thing:**
  - **For this repo's own development (ADR-019):** GitHub Spec Kit (`specify-cli` v0.15.1),
    `/speckit-specify` → `/speckit-plan` → `/speckit-tasks` → `/speckit-implement`, artifacts in
    `specs/<NNN>-<slug>/`. This is how contributors (human or AI) plan a feature before writing
    code — separate from `docs/adr/`, which is for standing architecture decisions.
  - **As a product feature for end users (ADR-018, and proposed further in ROADMAP_PLAN.md
    Milestone 7):** `requirements.md` + `software-design` playbook + `scaffold_project` skill,
    so a user describing a program gets clarifying questions and a written spec before any files
    get generated. Don't conflate the two — ADR-019 explicitly calls out that they're unrelated.
- **Dependency management via `uv`,** hybrid lock strategy (ADR-007): local `uv lock` for
  day-to-day work, container-resolved locks before releases/major merges.

## Key constraints

- Side effects go through approved execution paths (tools or approved skills), never free-form
  LLM behavior.
- Unapproved (`proposed`/`deprecated`) skills must not run.
- Playbooks are reasoning-only; they must never become executable.
- The runtime, not the LLM, enforces approval, validation, and sandbox boundaries.

## Current shape vs. what's dormant

Not everything that exists in the tree is live. Before citing a module as part of the
architecture, check it's actually imported somewhere:

- `py_mono/retrieval/keyword_ranker.py` — a playbook-scoring implementation that nothing
  currently imports. `PlaybookRegistry.search` (in `py_mono/playbook/`) has its own scoring and
  is what's actually in the loop.
- `py_mono/pods/`, `py_mono/mom/` — empty `__init__.py` stubs, no implementation. These track to
  "multi-agent orchestration" and are explicitly deprioritized in `docs/ROADMAP_PLAN.md`.

## Where this is going

Milestone-level sequencing (what's next, why, and what's explicitly gated on an audience
decision) lives in `docs/ROADMAP_PLAN.md` — not duplicated here. As of 2026-08-05 that's:
Milestone 6 (reliability foundation — CI, open issue fixes, model/task fitness check),
Milestone 7 (skill lifecycle graph — Critique/Test stages, diff-on-regeneration,
failure-driven evolution), Milestone 8 (signed skill provenance, gated on the "personal tool
vs. multi-user" question).

## History

- **2026-04-12** — original summary written (by Codex), covering through the early skills
  layer and ADR-008 provider-routing design. Archived at
  `docs/architectural-summary-by-codex-20260412.md`.
- **2026-08-05** — rewritten from scratch rather than patched, because four months of ADRs
  (ADR-010 through ADR-019: skills layer, interactive scaffolding, skills-vs-tools, approval
  chaining, `Tool.run`, dual-layer architecture, boundary enforcement, structured orchestration,
  project scaffolding, Spec Kit adoption) had made the old summary describe a mostly-superseded
  state. Also corrected two accuracy gaps found while writing this version: ADR-017's structured
  `action` field is actually implemented (the ADR header just never got updated from
  `Proposed`), and `py_mono/retrieval/keyword_ranker.py` is dead code, not part of the live
  playbook-matching path.
