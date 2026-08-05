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
| **Milestone** | Which `docs/ROADMAP_PLAN.md` milestone this belongs to (`—` if pre-roadmap / not milestone-tracked) |
| **Branch** | Branch working the issue, if any (`—` if none yet) |
| **Source** | Where it originated — audit report, session date, requester |

Every piece of tracked work gets an issue here, including items that originate as roadmap
candidates — see `docs/ROADMAP_PLAN.md`'s Authority Model. A roadmap milestone's scope should
resolve to `ISS-NNN` entries here, not stay as an un-filed bullet once work is about to start.

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

| ID | Status | Milestone | Title | Branch |
| --- | --- | --- | --- | --- |
| ISS-008 | open | Gated (M8 prereq) | Full isolated-worker execution for skills/dynamic tools | — |

## Closed Index

| ID | Status | Milestone | Title | Branch |
| --- | --- | --- | --- | --- |
| ISS-001 | done | M5 | App fails to import/start (syntax errors) | — |
| ISS-002 | done | M5 | `/workspace` sandbox escape via path-check bypass | fix-workspace-sandbox |
| ISS-003 | done | M5 | Skills/dynamic tools execute arbitrary code before approval | fix-skill-tool-approval-gate |
| ISS-004 | done | M5 | Add `kb-template/` portable knowledge-base scaffold | kb-template |
| ISS-005 | done | M6 | Pre-existing test failures unrelated to current branch work | fix-pre-existing-test-failures |
| ISS-006 | done | M6 | `pyyaml` used transitively but not declared as a direct dependency | add-pyyaml-direct-dependency |
| ISS-007 | done | M5 | Add dual Ollama backend selection with runtime model switching | ollama-dual-backend |
| ISS-009 | done | M5 | `OllamaProvider` returns empty content for thinking-capable models | fix-ollama-thinking-response |
| ISS-010 | done | M6 | Bare `/provider` silently falls through to the LLM | fix-bare-provider-command |
| ISS-011 | done | M6 | `generate_skill` output-quality gaps found dogfooding | fix-generate-skill-quality-issues |
| ISS-012 | done | M6 | Add minimal CI (`pytest` + `compileall` on every PR) | add-minimal-ci |
| ISS-013 | done | M6 | Add lightweight per-run telemetry log | add-skill-run-telemetry |
| ISS-014 | done | M6 | Add model/task fitness check | add-model-task-fitness-check |

---

## Open / Tracked — Detail

### ISS-008 — Full isolated-worker execution for skills/dynamic tools
- **Milestone:** Gated / deferred — prerequisite for M8, not part of M6
- **Source:** `docs/project-audit-2026-08-02.md` (C-03) remediation, deferred 2026-08-03 during
  ISS-003
- **What:** the audit's full C-03 recommendation was "execute approved extensions in an isolated
  worker with narrow tool RPC" — a materially larger infrastructure project (real
  process/container isolation plus a constrained tool-call protocol)
- **Scope:** explicitly out of scope for ISS-003's fix, which closed the "runs before approval"
  gap via a hash-ledger gate, not content-level sandboxing
- **Status:** tracked for future consideration, not started — also a prerequisite for
  Milestone 8 (`docs/ROADMAP_PLAN.md`), not just "eventually"

---

## Closed — Detail

### ISS-001 — App fails to import/start (syntax errors)
- **Milestone:** M5
- **Source:** `docs/project-audit-2026-08-02.md` (C-01)
- **Fix:** confirmed 2026-08-03: `python -m compileall -q py_mono skills kb-template` exits 0.
  Landed in commit `34e595e` ("fixed syntax errors and tested system")

### ISS-002 — `/workspace` sandbox escape via path-check bypass
- **Milestone:** M5
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
- **Milestone:** M5
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
- **Milestone:** M5
- **Source:** 2026-08-03 session
- **Fix:** landed in commits `1dd949f`, `b12cc64`, `c3f8f80` on branch `kb-template`
- **What:** reusable YAML front-matter + Obsidian-markdown scaffold with a standalone
  validator, extracted before further cross-project knowledge-base drift accumulates. See
  `specs/001-kb-template/`

### ISS-005 — Pre-existing test failures unrelated to current branch work
- **Milestone:** M6 — prerequisite for `ISS-012` (CI can't be green-required with known red tests)
- **Source:** discovered 2026-08-03 verifying `kb-template`
- **Fix:** landed on branch `fix-pre-existing-test-failures`. Three independent, unrelated
  failures:
  1. `skills/listallpy/skill.py` bypassed `context.agent_tools` entirely, walking the real
     filesystem directly via `Path(context.workspace_root).rglob("*.py")` — violated ADR-016
     and defeated `tests/test_listallpy_skill.py`'s `list_files` mock. Fixed by routing through
     `context.agent_tools["list_files"].run(path=".")` and filtering the returned JSON.
  2. `skills/.approvals.json`'s hash-ledger gate (ADR-013/ISS-003) hashed raw on-disk bytes,
     which git's `core.autocrlf` rewrites per checkout platform (CRLF on native Windows, LF on
     Linux/CI/Docker) even for byte-identical tracked content — silently invalidating
     `listallpy`'s approval. Verified systemic: 7 of 9 approved skills' ledger hashes would
     already mismatch a Linux checkout of the same content, which would have broken almost
     every skill's approval status the moment `ISS-012`'s CI ran. Fixed by normalizing
     `\r\n` → `\n` in `approval_ledger.hash_file()` before hashing and regenerating
     `skills/.approvals.json` under the corrected algorithm.
  3. `py_mono/tools/create_tool.py` had two message/contract mismatches against its own tests
     in `tests/tools/test_create_tool.py`, unrelated to the above: an inconsistent
     invalid-name message and a success message missing the written file's path (both brought
     in line with this module's own `"Error: ..."` convention and the sibling `write_file`
     tool's path-inclusion convention; two stale tests updated to match the tool's actual,
     already-relied-upon-elsewhere wrapped-`Tool`-schema contract).
- **Tests:** added `tests/test_approval_ledger.py` (3 tests: CRLF/LF hash equivalence, approval
  surviving a simulated re-checkout, a real content change still correctly invalidating
  approval). Full suite: 104 passed, 1 skipped (pre-existing, unrelated Windows symlink-privilege
  skip) — was 6 collection errors / 5 failures before. See
  `specs/006-fix-pre-existing-test-failures/`

### ISS-006 — `pyyaml` used transitively but not declared as a direct dependency
- **Milestone:** M6
- **Source:** discovered 2026-08-03 during `kb-template` planning; unbundled 2026-08-03 per
  external PR review
- **Fix:** landed on branch `add-pyyaml-direct-dependency`. Added `pyyaml` (unpinned) to the
  root `pyproject.toml`'s direct dependencies and regenerated `uv.lock`. Confirmed 4 direct
  `import yaml` call sites first (`py_mono/skill/validator.py`, `py_mono/skill/base.py`,
  `py_mono/playbook/playbookregistry.py`, `skills/generate_playbook/skill.py`)
- **History:** a fix was briefly bundled into the `kb-template` branch (commit `c3f8f80`) but
  reverted, since `kb-template`'s own `pyproject.toml` already declares `pyyaml` independently
  and doesn't need the root repo touched
- **Scope:** separate, pre-existing hygiene gap, not a `kb-template` requirement. See
  `specs/007-add-pyyaml-direct-dependency/`

### ISS-007 — Add dual Ollama backend selection with runtime model switching
- **Milestone:** M5
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
- **Milestone:** M5
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

### ISS-010 — Bare `/provider` silently falls through to the LLM
- **Milestone:** M6
- **Source:** 2026-08-05 session, user hit it live in the CLI
- **Fix:** landed on branch `fix-bare-provider-command`. `py_mono/agent/agent.py`'s
  `_is_special_command`/`_handle_special_command` only matched `text.startswith("/provider ")`
  (trailing space + argument required) or the exact string `/providers`. Added the exact string
  `"/provider"` to the recognized-commands tuple and a matching branch returning
  `"Usage: /provider <provider> [model]"` (the same message already used for the
  trailing-space case)
- **Reproduced live before the fix:** bare `/provider` produced an LLM reply ("What specific
  type of \"provider\" were you asking about?"); `/provider ollama-auto
  qwen2.5-coder:7b-instruct-q5_K_M` (the correct form) switched providers normally
- **Tests:** added `tests/test_special_commands.py` (5 tests: bare `/provider` recognized +
  shows usage, trailing-space-only unaffected, `/providers` unaffected, valid-argument switching
  unaffected). See `specs/008-fix-bare-provider-command/`

### ISS-011 — `generate_skill` output-quality gaps found dogfooding
- **Milestone:** M6
- **Source:** 2026-08-05 session, user hit it live running
  `/skill generate_skill listallpy | ...` after switching to a coding-tuned model; reviewed with
  claude.ai, both findings re-verified against the actual code before filing
- **Context:** three related findings from one *successful* (not failing) run — the underlying
  ISS-009 fix worked; these are quality/robustness gaps in `generate_skill` itself
- **Fix:** landed on branch `fix-generate-skill-quality-issues`. Two code fixes plus one
  non-code investigation:
  1. **Fence-stripping** — `_strip_markdown_fences()` (`py_mono/skill/validator.py`) rewritten
     to find a fenced code block via regex anywhere in the text, instead of requiring the
     string to start with a fence. Fixes trailing-only fences and preamble-before-fence output.
     Added `tests/test_skill_validator.py` (7 tests).
  2. **Leaked template placeholder** — `py_mono/skill/prompts.py`'s
     `build_skill_md_prompt()` fillable sections (paragraph description, expected output,
     constraints) now marked with explicit `[INSTRUCTION — ...]` prefixes, plus a closing rule
     telling the model never to copy an instruction marker into its output. Added
     `tests/test_skill_prompts.py` (3 tests).
  3. **CPU-bound/unoffloaded inference** — investigated directly against the reachable
     `OLLAMA_REMOTE_URL` (`http://100.105.24.12:11434`): `/api/ps` after loading
     `qwen2.5-coder:7b-instruct-q5_K_M` (the model from the original report) showed
     `size_vram: 0` against a ~5.8 GB model — confirmed with a second model, also `size_vram: 0`.
     The remote backend is not GPU-offloading inference at all, for any model tested, which
     explains the originally-reported near-parity throughput. Not a code fix in this repo — see
     `specs/009-generate-skill-quality-issues/research.md`. *Why* GPU offload isn't happening
     would need direct access to that host's own system, out of this session's reach.

### ISS-012 — Add minimal CI (`pytest` + `compileall` on every PR)
- **Milestone:** M6
- **Source:** filed 2026-08-05 from `docs/ROADMAP_PLAN.md` M6 scope
- **Fix:** landed on branch `add-minimal-ci`. Added `.github/workflows/ci.yml`: triggers on
  `pull_request` and `push` to `main`, runs on `ubuntu-latest`, installs `uv`
  (`astral-sh/setup-uv`), runs `uv sync --group dev`, `uv run pytest -q`, and
  `uv run python -m compileall -q py_mono skills`
- **Depended on:** `ISS-005` (fixed, `#96`) — validated locally by merging that fix into this
  branch before adding CI, so the workflow's commands were confirmed green (104 passed, 1
  skipped, compileall clean) rather than assumed
- **Scope note:** adds the workflow only — making it *required* (branch protection blocking
  merge on failure) is a separate, repo-owner-only GitHub settings change, intentionally not
  done as part of this item. See `specs/010-add-minimal-ci/`

### ISS-013 — Add lightweight per-run telemetry log
- **Milestone:** M6
- **Source:** filed 2026-08-05 from `docs/ROADMAP_PLAN.md` M6 scope (originally described as a
  shared dependency for M7, pulled forward into M6 since `ISS-014` needs it and M6 ships first)
- **Fix:** landed on branch `add-skill-run-telemetry`. New `py_mono/skill/telemetry.py`
  (`log_skill_run`/`read_skill_runs`) appends one JSON line per skill run to
  `telemetry/skill_runs.jsonl` (`skill`, `provider`, `model`, `duration_ms`, `success`,
  `timestamp`); a write failure logs a warning and never breaks skill execution. Hooked into
  `run_skill_safe` (`py_mono/skill/approval.py`) — the single existing chokepoint every skill
  execution already passes through — via `try/finally`, so both successful and failed runs are
  logged. `telemetry/` added to `.gitignore` (matching the existing `workspace/`/
  `dynamic_tools/` pattern; operational data, not source). Added `tests/test_skill_telemetry.py`
  (5 tests) and 3 new tests in `tests/test_skill_approval.py`. See
  `specs/011-add-skill-run-telemetry/`

### ISS-014 — Add model/task fitness check
- **Milestone:** M6
- **Source:** filed 2026-08-05 from `docs/ROADMAP_PLAN.md` M6 scope
- **Fix:** landed on branch `add-model-task-fitness-check`. New `py_mono/skill/fitness.py`:
  `check_model_fitness(skill, provider, model)` reads `ISS-013`'s telemetry log, and — only once
  at least 3 recorded runs exist for the exact (skill, provider, model) combination — warns if
  at least half of the most recent 5 matching runs failed. Hooked into `run_skill_safe`
  (`py_mono/skill/approval.py`): a warning (if any) is prepended to a successful result; a
  failed run attaches no warning (its own exception is already the signal). Directly
  productizes the `ISS-009`/`ISS-011` lesson (thinking models reasoning verbosely/unreliably on
  template-filling tasks) as an evidence-based check, not a hardcoded list of "bad" models.
  Added `tests/test_skill_fitness.py` (6 tests) and 3 new tests in
  `tests/test_skill_approval.py`. See `specs/012-add-model-task-fitness-check/`
