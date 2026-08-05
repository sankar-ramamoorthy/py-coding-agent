---
title: Issues Register
type: index
status: canonical
created: 2026-08-03
updated: 2026-08-05
---

# Issues Register

## Purpose

Lightweight, local issue tracker for py-coding-agent runtime work. Not a substitute for
`docs/adr/` (standing architecture decisions) or `specs/` (Spec Kit per-feature plans) — this
file tracks discrete, open pieces of work and known problems across sessions.

## Fields

| Field | Meaning |
| --- | --- |
| **ID** | Sequential, prefixed `ISS-NNN` (zero-padded, 3 digits, monotonically increasing, never reused) |
| **Title** | Short description |
| **Status** | See Status Values below |
| **Branch** | Branch working the issue, if any (`—` if none yet) |
| **Source** | Where it originated — audit report, session date, requester |

Longer context (root cause, fix details, links to files/ADRs/commits/specs) lives in each
issue's own section below the index, not in the index table — keeps the table scannable.

## Status Values

- `open` — not started
- `in-progress` — actively being worked
- `blocked` — cannot proceed without a resolved dependency or decision
- `done` — accepted as complete
- `wontfix` — intentionally not implemented

---

## Open / Tracked Index

| ID | Status | Title | Branch |
| --- | --- | --- | --- |
| ISS-005 | open | Pre-existing test failures unrelated to current branch work | — |
| ISS-006 | open | `pyyaml` used transitively but not declared as a direct dependency | — |
| ISS-008 | open | Full isolated-worker execution for skills/dynamic tools | — |
| ISS-010 | open | Bare `/provider` silently falls through to the LLM | — |
| ISS-011 | open | `generate_skill` output-quality gaps found dogfooding | — |

## Closed Index

| ID | Status | Title | Branch |
| --- | --- | --- | --- |
| ISS-001 | done | App fails to import/start (syntax errors) | — |
| ISS-002 | done | `/workspace` sandbox escape via path-check bypass | fix-workspace-sandbox |
| ISS-003 | done | Skills/dynamic tools execute arbitrary code before approval | fix-skill-tool-approval-gate |
| ISS-004 | done | Add `kb-template/` portable knowledge-base scaffold | kb-template |
| ISS-007 | done | Add dual Ollama backend selection with runtime model switching | ollama-dual-backend |
| ISS-009 | done | `OllamaProvider` returns empty content for thinking-capable models | fix-ollama-thinking-response |

---

## Open / Tracked — Detail

### ISS-005 — Pre-existing test failures unrelated to current branch work
- **Source:** discovered 2026-08-03 verifying `kb-template`
- **What:**
  - `tests/test_listallpy_skill.py` fails to collect (`ModuleNotFoundError: No module named
    'skills'`)
  - `tests/tools/test_create_tool.py` has 2 failing assertions
    (`test_create_tool_writes_file_for_valid_name`, `test_create_tool_rejects_invalid_module_name`)
    — behavior doesn't match test expectations
- **Confirmed pre-existing** by reproducing identically with `kb-template`'s changes stashed
- **Scope:** not fixed as part of `kb-template` — out of scope, unrelated concern per
  Constitution Principle I
- **Why it matters now:** blocks Milestone 6 CI from being green-required (see
  `docs/ROADMAP_PLAN.md`) — can't gate merges on a suite with known, undiagnosed red tests

### ISS-006 — `pyyaml` used transitively but not declared as a direct dependency
- **Source:** discovered 2026-08-03 during `kb-template` planning; unbundled 2026-08-03 per
  external PR review
- **What:** `py_mono/skill/validator.py`, `py_mono/skill/base.py`, and
  `py_mono/playbook/playbookregistry.py` all `import yaml` directly, but it's only ever
  resolved transitively (via `litellm`/`fastmcp`), never declared as a direct dependency
- **History:** a fix was briefly bundled into the `kb-template` branch (commit `c3f8f80`) but
  reverted, since `kb-template`'s own `pyproject.toml` already declares `pyyaml` independently
  and doesn't need the root repo touched
- **Scope:** separate, pre-existing hygiene gap, not a `kb-template` requirement

### ISS-008 — Full isolated-worker execution for skills/dynamic tools
- **Source:** `docs/project-audit-2026-08-02.md` (C-03) remediation, deferred 2026-08-03 during
  ISS-003
- **What:** the audit's full C-03 recommendation was "execute approved extensions in an isolated
  worker with narrow tool RPC" — a materially larger infrastructure project (real
  process/container isolation plus a constrained tool-call protocol)
- **Scope:** explicitly out of scope for ISS-003's fix, which closed the "runs before approval"
  gap via a hash-ledger gate, not content-level sandboxing
- **Status:** tracked for future consideration, not started — also a prerequisite for
  Milestone 8 (`docs/ROADMAP_PLAN.md`), not just "eventually"

### ISS-010 — Bare `/provider` silently falls through to the LLM
- **Source:** 2026-08-05 session, user hit it live in the CLI
- **What:** `py_mono/agent/agent.py`'s `_is_special_command`/`_handle_special_command` only
  match `text.startswith("/provider ")` (trailing space + argument required) or the exact
  string `/providers`. Bare `/provider` (no space, no argument) matches neither, so it's routed
  to the LLM as a normal chat message instead of showing usage
- **Reproduced live:** bare `/provider` produced an LLM reply ("What specific type of
  \"provider\" were you asking about?"); `/provider ollama-auto qwen2.5-coder:7b-instruct-q5_K_M`
  (the correct form) switched providers normally
- **Fix:** deferred — to be routed through Spec Kit (specify → plan → tasks → implement) per
  explicit instruction, not fixed inline

### ISS-011 — `generate_skill` output-quality gaps found dogfooding
- **Source:** 2026-08-05 session, user hit it live running
  `/skill generate_skill listallpy | ...` after switching to a coding-tuned model; reviewed with
  claude.ai, both findings re-verified against the actual code before filing
- **Context:** three related findings from one *successful* (not failing) run — the underlying
  ISS-009 fix worked; these are quality/robustness gaps in `generate_skill` itself
- **What:**
  1. **Fence-stripping isn't symmetric-only safe** — `_strip_markdown_fences()`
     (`py_mono/skill/validator.py:233`) only strips a leading fence if the whole output starts
     with one, and only strips a trailing fence if a leading one was already found. A
     trailing-only fence leaves a stray `` ``` `` in the output; any preamble before the fence
     (e.g. "Here's the code:\n```python...") isn't stripped at all and would fail `ast.parse()`
     outright. Didn't manifest this run only because the model happened to fence symmetrically
     with no preamble.
  2. **Leaked template placeholder line** — `py_mono/skill/prompts.py:90` contains `- List each
     constraint as a bullet point.`, phrased identically to a real constraint bullet, with
     nothing marking it as instructional text to replace rather than content to keep. The model
     echoed it back verbatim as a "constraint" in the generated `SKILL.md` (confirmed in the
     transcript).
  3. **Possible CPU-bound/unoffloaded inference** — both `generate_skill` LLM calls this run
     showed prompt-processing throughput (~15 tok/s) in the same order of magnitude as
     generation throughput (~6 tok/s); on GPU, prompt processing is normally an order of
     magnitude faster than autoregressive generation, so near-parity suggests CPU-bound or
     partial-GPU-offload inference — needs investigating via `ollama ps` or server-side GPU
     offload logs, not a code fix in this repo.
- **Fix:** deferred — to be routed through Spec Kit per explicit instruction, not fixed inline

---

## Closed — Detail

### ISS-001 — App fails to import/start (syntax errors)
- **Source:** `docs/project-audit-2026-08-02.md` (C-01)
- **Fix:** confirmed 2026-08-03: `python -m compileall -q py_mono skills kb-template` exits 0.
  Landed in commit `34e595e` ("fixed syntax errors and tested system")

### ISS-002 — `/workspace` sandbox escape via path-check bypass
- **Source:** `docs/project-audit-2026-08-02.md` (C-02)
- **Fix:** landed in commits `71a9ffa`, `ad8eb20` on branch `fix-workspace-sandbox`
  - Real path containment (`Path.is_relative_to`) replaces the string-prefix check
  - New empty-by-default `ADDITIONAL_ALLOWED_PATHS` allowlist
  - `shell` tool now opt-in via `ENABLE_SHELL_TOOL` (default false), 30s timeout, description
    corrected to not overstate its safety
  - `docker-compose.yml`'s `.:/app` mount is now read-only
  - `docs/adr/ADR-001` corrected (Proposed → Accepted)
- **Verification:** both original bugs live-demonstrated pre-fix and the fix verified for real,
  post-fix, inside the actual running container (not just mocked tests). See
  `specs/003-fix-workspace-sandbox/`

### ISS-003 — Skills/dynamic tools execute arbitrary code before approval
- **Source:** `docs/project-audit-2026-08-02.md` (C-03)
- **Fix:** landed in commits `d4cddfa`, `f542ccc` on branch `fix-skill-tool-approval-gate`
  - `SkillRegistry.load()`/`reload_skill()` gated on a hash-ledger approval record
    (`skills/.approvals.json`, content hash of `skill.py` at approval time — not just the
    in-file status field) before `exec_module` runs; editing `skill.py` post-approval
    invalidates it
  - `/approve` re-validates current `skill.py` via `validate_skill_py` before writing the ledger
  - The 8 pre-existing approved skills auto-seeded with zero disruption
  - `ENABLE_DYNAMIC_TOOLS` (default false) gates dynamic-tool auto-loading, mirroring ISS-002's
    `ENABLE_SHELL_TOOL`
  - Static forbidden-pattern/AST validation added before `exec_module` and before
    `create_tool()` writes to disk
  - `docs/adr/ADR-013` corrected
- **Deferred:** full isolated-worker execution — tracked as ISS-008
- **Verification:** bug live-demonstrated pre-fix and the exact fix verified live, post-fix,
  inside the real container. See `specs/004-fix-skill-tool-approval-gate/`

### ISS-004 — Add `kb-template/` portable knowledge-base scaffold
- **Source:** 2026-08-03 session
- **Fix:** landed in commits `1dd949f`, `b12cc64`, `c3f8f80` on branch `kb-template`
- **What:** reusable YAML front-matter + Obsidian-markdown scaffold with a standalone
  validator, extracted before further cross-project knowledge-base drift accumulates. See
  `specs/001-kb-template/`

### ISS-007 — Add dual Ollama backend selection with runtime model switching
- **Source:** 2026-08-03 session, user request
- **Fix:** landed in commits `bf1e23b`, `550a51d` on branch `ollama-dual-backend`
- **What:** adds `ollama-remote`/`ollama-local`/`ollama-auto` `provider_registry.py` entries
  wrapping the existing `OllamaProvider` (new optional `base_url` param) plus a
  connectivity-probe fallback (`ollama-auto` prefers remote GPU desktop over Tailscale, falls
  back to local). Model switching works via the existing `/provider <name> <model>` command, no
  command-dispatch changes
- **Verification:** verified end-to-end against the real backends, not just mocked tests. See
  `specs/002-ollama-dual-backend/`

### ISS-009 — `OllamaProvider` returns empty content for thinking-capable models
- **Source:** 2026-08-05 session, user hit it live via `/skill generate_skill`
- **What:** `OllamaProvider.generate()` sent no `think`/`num_predict`/`num_ctx`, letting a
  thinking-capable model (e.g. `qwen3.5:4b`) exhaust its budget on internal reasoning and return
  empty content
- **Fix:** landed in commit `8acaede` on branch `fix-ollama-thinking-response`
  - `think: false` by default (`OLLAMA_ENABLE_THINKING`) — empirically confirmed to eliminate
    reasoning cost entirely for models with native Ollama thinking support (`qwen3.5:4b`, the
    model from the original bug report)
  - `options.num_predict`/`num_ctx` (`OLLAMA_NUM_PREDICT`/`OLLAMA_NUM_CTX`) as a safety net for
    models that ignore the `think` field (`lfm2.5-thinking:latest`, this repo's own local
    default)
  - Raised the previously-hardcoded 300s request timeout to `OLLAMA_REQUEST_TIMEOUT` (now
    600s), needed once real testing showed the safety-net path alone could exceed it
- **Notes:** both the original chat-based diagnosis and an initial round of testing pointed the
  wrong way before testing against the actual model from the bug report corrected the design —
  see `specs/005-fix-ollama-thinking-response/research.md` for the full empirical trail. Raw
  capture: `kb-template/knowledge/raw/brainstorm-20260805-ollama-thinking-empty-response.md`
