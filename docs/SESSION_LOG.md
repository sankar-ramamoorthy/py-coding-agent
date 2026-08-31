# Session Log

Append-only. One entry per work session, newest at the bottom. Use the Completion Report
Format (see AGENTS.md, Session Completion) for each entry.

---

## 2026-08-03 — kb-template branch bootstrap
**Issue**: ISS-004 (kb-template scaffold) + process-doc bootstrap

**Scope completed**:
- Bootstrapped repo process docs that didn't previously exist: `docs/ISSUES.md`,
  `docs/PROJECT_STATUS.md`, `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md`,
  `docs/SESSION_LOG.md`, and a new "Session Completion" section in `AGENTS.md`
  documenting the Completion Report Format.
- Ran the full Spec Kit cycle (first ever in this repo) for the kb-template feature:
  `specs/001-kb-template/{spec,plan,research,data-model,quickstart}.md`,
  `contracts/validator-cli.md`, `checklists/requirements.md`, `tasks.md` (31 tasks).
- Implemented `kb-template/`: front-matter schema (`docs/schema.md` + `validator/schema.py`),
  the raw/processed/topics/index folder lifecycle, promotion rule doc, authoring-rules doc,
  one example document per `type`, and a standalone Python validator (own `pyproject.toml`,
  PyYAML only) checking schema compliance, wikilink resolution, and the promotion rule.
- Added `tests/kb_template/test_validate.py` (15 cases) and declared `pyyaml` explicitly
  in the root `pyproject.toml` (previously only a transitive dependency).

**Files changed**: See commits `1dd949f` (process bootstrap), `b12cc64` (Spec Kit
artifacts), `c3f8f80` (kb-template implementation) on branch `kb-template`. Also this
commit's session-doc updates (`docs/ISSUES.md`, `docs/SESSION_LOG.md`,
`docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md`).

---

## 2026-08-05 — README/KB doc-drift cleanup, capture-brainstorm-note skill, fix ISS-009 (Ollama thinking-model empty response)

**Issue**: Started from a user-run claude.ai doc-freshness audit of `README.md`; expanded into
several related pieces of work in one session: doc-drift fixes, a new project skill, filing and
fixing a real bug (ISS-009) hit live during the session.

**Scope completed**:
- **README/kb-template doc-drift** (PR #83): consolidated three duplicated/drifted "skills"
  sections in `README.md` into one pointer at `README_Skills.md`/`docs/skills.md`; removed a
  broken orphan code fence; fixed a stale `docs/README_Skills.md` path (the file actually lives
  at repo root); fixed `README_Skills.md`'s own unclosed code-fence wrapper; stripped leftover
  LLM chat preamble from `docs/skills.md`; gave the roadmap's orphaned Milestone 5 bullets a
  proper heading matching M1-M4's style.
- **py-coding-agent lifecycle one-pager + cross-project reference redaction** (PR #84): added
  `kb-template/knowledge/raw/py-coding-agent_Lifecycle_Graph_OnePager.md` (scoped only to this
  repo, per explicit user instruction not to reference other projects); deleted a stray
  TradeForge-scoped draft of the same file; genericized four pre-existing docs
  (`docs/ISSUES.md`, `docs/NEXT_ACTIONS.md`, `docs/SESSION_LOG.md`,
  `specs/001-kb-template/spec.md`) that had named specific outside projects, replacing the names
  with generic phrasing while keeping the underlying rationale.
- **`capture-brainstorm-note` skill + file/spec ISS-009** (PR #85): added a project-scoped
  Claude Code skill (`.claude/skills/` + `.agents/skills/` mirror) adapted to this repo's actual
  `kb-template` schema; used it to capture a real bug hit live via `/skill generate_skill`
  (Ollama returning empty content for thinking-capable models); filed `docs/ISSUES.md` ISS-009;
  ran it through Spec Kit's specify phase (`specs/005-fix-ollama-thinking-response/spec.md` +
  checklist) — capture and spec only, no fix, per explicit instruction to route the fix through
  spec-driven development rather than hot-patch from chat.
- **Fix ISS-009** (this session, branch `fix-ollama-thinking-response`, not yet merged): ran
  `/speckit-plan` and `/speckit-tasks`, then implemented. The fix went through two rounds of
  empirical correction during planning — see `specs/005-fix-ollama-thinking-response/research.md`
  for the full account:
  - Initially (following the original chat-based diagnosis) tested `think: false` against this
    repo's *local* default model (`lfm2.5-thinking:latest`) and found it didn't suppress
    reasoning at all — looked like clear grounds to reject it and rely on
    `options.num_predict`/`num_ctx` alone.
  - Testing against the *actual* model from the bug report (`qwen3.5:4b`, on the configured
    remote host) reversed that conclusion: `think: false` genuinely eliminates reasoning and its
    token cost for that model (`eval_count: 3` for a trivial prompt, vs. thousands when
    reasoning). Final design uses both: `think: false` by default
    (`OLLAMA_ENABLE_THINKING`, default off) as the primary, near-zero-cost fix for compliant
    models, plus `options.num_predict`/`num_ctx` (`OLLAMA_NUM_PREDICT=4096`,
    `OLLAMA_NUM_CTX=8192`) as a safety net for non-compliant models like `lfm2.5-thinking`.
  - Also discovered mid-implementation: the previously-hardcoded `requests.post(timeout=300)`
    was insufficient for the safety-net path alone (raised `ReadTimeout` in real testing against
    `qwen3.5:4b` at `num_predict=4096`) — raised to `OLLAMA_REQUEST_TIMEOUT` (default 600s).
  - The final exact payload combination (`think: false` + budget) was validated end-to-end
    against both real models this agent actually uses, not just individually or via mocks.

**Files changed**:
- PR #83: `README.md`, `README_Skills.md`, `docs/skills.md`.
- PR #84: `kb-template/knowledge/raw/py-coding-agent_Lifecycle_Graph_OnePager.md` (added),
  `kb-template/knowledge/raw/TradeForge_Lifecycle_Graph_OnePager.md` (deleted, untracked),
  `docs/ISSUES.md`, `docs/NEXT_ACTIONS.md`, `docs/SESSION_LOG.md`, `specs/001-kb-template/spec.md`.
- PR #85: `.claude/skills/capture-brainstorm-note/SKILL.md`, `.agents/skills/capture-brainstorm-note/SKILL.md`,
  `kb-template/knowledge/raw/brainstorm-20260805-ollama-thinking-empty-response.md`,
  `docs/ISSUES.md`, `.specify/feature.json`, `specs/005-fix-ollama-thinking-response/spec.md`,
  `specs/005-fix-ollama-thinking-response/checklists/requirements.md`.
- This session (commit `8acaede`, branch `fix-ollama-thinking-response`, not yet merged):
  `py_mono/config.py`, `py_mono/llm/ollama_provider.py`, `tests/llm/test_ollama_provider.py`,
  `docs/ISSUES.md`, `specs/005-fix-ollama-thinking-response/{plan,research,data-model,quickstart,tasks}.md`,
  `specs/005-fix-ollama-thinking-response/contracts/ollama-chat-request-contract.md`.

**Design decisions**:
- Fix lives entirely in the shared `OllamaProvider` (constitution Principle II), not per-skill —
  every Ollama-backed call in the agent benefits, not just `generate_skill`.
- Chose empirical testing against real running Ollama servers (both local and the configured
  remote host) over trusting either the original chat-based diagnosis or a first round of
  incomplete testing — the two corrections during planning (see above) would not have been
  caught otherwise, and materially changed the final design.
- Kept `docs/ISSUES.md`, `docs/NEXT_ACTIONS.md`, `docs/SESSION_LOG.md`, and
  `specs/001-kb-template/spec.md` free of references to projects outside this repo, per explicit
  user instruction — redacted specific project names to generic phrasing rather than deleting
  the underlying historical reasoning.

**Validation**:
- `pytest tests/llm/test_ollama_provider.py -v` — 11/11 passed (7 new tests added for this
  feature, 4 pre-existing).
- `pytest -q --ignore=tests/test_listallpy_skill.py` — 97 passed, 1 skipped, 2 failed (both the
  pre-existing, already-tracked `ISS-005` failures — unrelated, unchanged by this work).
- `kb-template/validator/validate.py .` — 16/16 files passed (run during PR #84/#85 work).
- Empirical end-to-end validation against real Ollama servers (not just mocks) for the exact
  payload shape now shipped, against both `qwen3.5:4b` (remote) and `lfm2.5-thinking:latest`
  (local) — see `specs/005-fix-ollama-thinking-response/research.md` for full transcripts and
  reasoning.

**Open items**:
- `fix-ollama-thinking-response` branch not yet pushed/merged (implementation commit `8acaede`;
  `docs/ISSUES.md` ISS-009 already flipped to `done` referencing that hash, matching how
  ISS-002/ISS-003 cite their branch's own commits rather than waiting for the merge commit —
  this repo merges via real merge commits, so the hash persists on `main` after merge).
- Model-swap follow-up (lighter, non-thinking, code-tuned model for structured generation tasks)
  discussed and left as an explicit, separate, undecided next action — see
  `docs/NEXT_ACTIONS.md` and `docs/CURRENT_FOCUS.md`.
- `ISS-005`, `ISS-006`, `ISS-008` remain open, untouched by this session.

**Next safe action**: Review the `fix-ollama-thinking-response` branch, push, and open a PR into
`main`.

**Design decisions**:
- `kb-template/` ships its own minimal `pyproject.toml` (PyYAML only) rather than relying
  on this repo's environment, so it's genuinely standalone-portable — verified by running
  it from inside `kb-template/`, which builds its own independent `.venv`.
- Meta/instructional files (top-level `README.md`, `docs/*.md`, `validator/README.md`, and
  the folder-explainer `README.md`s under `knowledge/*/`) intentionally carry **no** front
  matter — only `examples/*.md` are schema-bearing "documents." A file with no opening
  `---` is treated as prose, not a KB document, and isn't schema/promotion-checked (though
  its wikilinks still are).
- The validator strips fenced/inline code spans before scanning for `[[wikilinks]]`, so
  illustrative syntax shown in prose (e.g. `` `[[example]]` ``) isn't mistaken for a real,
  unresolved link — discovered as a real bug during verification, not anticipated in the plan.
- Added `[tool.setuptools.packages.find]` to `kb-template/pyproject.toml` — setuptools'
  flat-layout auto-discovery otherwise errors on multiple top-level dirs (`knowledge/`,
  `validator/`).

**Validation**:
- `python -m compileall -q py_mono skills kb-template` — exit 0 (also confirms ISS-001 fixed).
- `pytest` (full suite, excluding one pre-existing broken collection) — 20 passed, 2
  pre-existing failures (see ISS-005), 0 regressions from this work.
- `pytest tests/kb_template/ -v` — 15/15 passed.
- Validator run against the shipped `kb-template/` scaffold, both invocation styles (from
  inside `kb-template/` with its own fresh `.venv`, and via `uv run --project kb-template`
  from the repo root) — 13/13 files pass, exit 0.
- Manually ran quickstart.md Scenarios 2–5 (missing field, invalid enum, broken wikilink,
  promotion-rule violation) against scratch copies — each failed with the specific,
  documented message and exit code 1.

**Open items**:
- ISS-002, ISS-003 (sandbox/execution security issues) — untouched, deliberately out of
  scope for this branch.
- ISS-005 (pre-existing test failures) — newly logged, not fixed, unrelated to this work.
- kb-template/ repo split, migrating other internal knowledge-base projects onto this schema,
  and CI/pre-commit wiring for the validator all remain explicitly deferred future work.
- Branch `kb-template` has not been pushed or opened as a PR — left ready locally per
  the session's scope (no merge/push authorized).

**Next safe action**: Review the `kb-template` branch's 3 commits, then push and open a
PR into `main` when ready (this repo's `ms5-skills`/Spec Kit scaffold is also not yet on
`main` — the PR will carry both). Separately, decide whether to start on ISS-002/ISS-003
(the original C-02/C-03 audit findings) next, per the user's original "even before fixing
C-01 through C-03" framing.

---

## 2026-08-03 — kb-template: post-review fixes (PR #79)
**Issue**: External code review of PR #79 (kb-template) flagged two issues to resolve
before merge.

**Scope completed**:
- Reverted the root `pyproject.toml`/`uv.lock` explicit `pyyaml` dependency added in
  `c3f8f80`. It wasn't actually required by kb-template (which already declares `pyyaml`
  independently in its own `pyproject.toml` per FR-011/FR-015) — it was an unrelated,
  pre-existing hygiene fix (an undeclared transitive dependency) bundled into a feature
  whose own spec says it must not depend on this repo's runtime. Logged separately as
  ISS-006 instead.
- Added `kb-template/examples/example-adr.md`, the missing fourth example for the `adr`
  `type` value (FR-002 defines four `type` values; FR-014 previously only required
  examples for three of them, with no stated reason for the gap). Updated FR-014 in
  `specs/001-kb-template/spec.md` to require all four. Also cross-linked it from
  `example-canonical-doc.md`'s `related:` field and body.

**Files changed**: `pyproject.toml`, `uv.lock` (reverted), `docs/ISSUES.md` (added
ISS-006), `specs/001-kb-template/spec.md` (FR-014), `kb-template/examples/example-adr.md`
(new), `kb-template/examples/example-canonical-doc.md` (cross-link update).

**Design decisions**:
- Chose to add the missing example rather than just document the gap with a note —
  kb-template is meant to be a generic, self-demonstrating scaffold, and all four `type`
  values should get equal treatment. The new example itself notes that a project with its
  own existing ADR convention (like this repo's `docs/adr/`) isn't obligated to migrate
  onto kb-template's schema for ADRs specifically.

**Validation**:
- Confirmed `pyyaml` still resolves transitively after removing the explicit root
  dependency (`import yaml` still succeeds); re-ran `pytest` — same 20 passed / 2
  pre-existing failures (ISS-005) as before, zero change in behavior.
- Re-ran the validator against the shipped `kb-template/` scaffold — now 14/14 files
  pass (up from 13, with the new example included), exit 0.

**Open items**: ISS-006 (root `pyproject.toml` pyyaml declaration) — logged, not fixed,
tracked as separate future work.

**Next safe action**: Commit and push these fixes to update PR #79, then it's ready for
merge review.

---

## 2026-08-03 — Dual Ollama backend selection (local + remote GPU)
**Issue**: ISS-007

**Scope completed**:
- Registered `ISS-007`, ran the full Spec Kit cycle (second feature in this repo):
  `specs/002-ollama-dual-backend/{spec,plan,research,data-model,quickstart}.md`,
  `contracts/provider-selection.md`, `checklists/requirements.md`, `tasks.md` (23 tasks).
- Added `ollama-remote`/`ollama-local`/`ollama-auto` entries to
  `py_mono/llm/provider_registry.py`'s `REGISTRY`, all wrapping the existing
  `OllamaProvider` (given a new optional `base_url` constructor parameter in
  `py_mono/llm/ollama_provider.py`).
- Added `py_mono/llm/ollama_connectivity.py` (`is_ollama_reachable`) — a one-time,
  2-second-timeout reachability probe used only by `ollama-auto`.
- Changed `LLM_PROVIDER`'s default from `"ollama"` to `"ollama-auto"` in
  `py_mono/config.py`; updated `.env.example` and `docker-compose.yml` with the four new
  env vars (`OLLAMA_REMOTE_URL`, `OLLAMA_REMOTE_MODEL`, `OLLAMA_LOCAL_URL`,
  `OLLAMA_LOCAL_MODEL`).
- Added `tests/llm/` (3 files, 22 tests) and `tests/session/test_session_manager.py`
  (5 tests) — all mocked, zero real network calls in the automated suite.

**Files changed**: See commits `bf1e23b` (issue + Spec Kit artifacts), `550a51d`
(implementation) on branch `ollama-dual-backend`. Also this commit's session-doc updates.

**Design decisions**:
- Bare `ollama` kept completely frozen (still only reads `OLLAMA_BASE_URL`/`OLLAMA_MODEL`,
  no probing) for full backward compatibility — confirmed explicitly with the user before
  implementation, since redefining it would have silently changed existing behavior.
- `ollama-remote`/`ollama-local` never probe reachability — failures surface as direct,
  real connection errors, distinct from `ollama-auto`'s silent fallback. Confirmed by a
  dedicated test (`test_explicit_backends_never_probe_reachability`) and by real-backend
  verification (Scenario 4).
- The reachability probe lives in its own small module (`ollama_connectivity.py`) rather
  than inline in `provider_registry.py`, so it's independently mockable without importing
  the whole registry.
- No changes to `py_mono/agent/agent.py`'s command dispatch, the shell tool, dynamic-tool
  loading, or the execution loop — confirmed during planning that the existing
  `/provider <name> <model>` command already threads any new registry name through with
  zero code changes there.

**Validation**:
- `python -m compileall -q py_mono` — exit 0.
- `pytest` (full suite, excluding the pre-existing broken `test_listallpy_skill.py`
  collection) — 47 passed, 2 pre-existing failures (ISS-005, confirmed unaffected/unrelated
  to this branch), 0 regressions from this feature.
- Real, non-mocked verification inside the Docker container (matching actual usage, since
  `host.docker.internal` doesn't resolve from the host directly) against both live
  backends: `ollama-auto` resolved to remote and returned a real chat response;
  `ollama-remote`/`ollama-local` explicit selection both worked; model override to
  `qwen3:4b` on the remote backend worked and correctly reverted to `qwen3.5:4b` on the
  next selection with no override; forcing the remote URL unreachable made `ollama-auto`
  fall back to local within 2.02s (the probe timeout); the same forced-unreachable address
  under an *explicit* `ollama-remote` selection raised a real `ConnectionError` rather than
  silently falling back; `LLM_PROVIDER=ollama` (legacy) resolved byte-for-byte as before.

**Open items**:
- ISS-002, ISS-003 (sandbox/execution security issues) — untouched, deliberately out of
  scope for this branch, per the user's original "even before fixing C-01 through C-03"
  framing (still not started).
- ISS-005, ISS-006 — pre-existing, unrelated, not fixed here.
- Branch `ollama-dual-backend` has not been pushed or opened as a PR — left ready locally.

**Next safe action**: Review the `ollama-dual-backend` branch's 2 commits (plus this
session-doc commit), then push and open a PR into `main` when ready. Separately, decide
whether ISS-002/ISS-003 (the original C-02/C-03 security findings) are next.

---

## 2026-08-03 — Fix workspace sandbox escape (ISS-002)
**Issue**: ISS-002

**Scope completed**:
- Registered/updated `ISS-002`, ran the third full Spec Kit cycle (4 user stories):
  `specs/003-fix-workspace-sandbox/{spec,plan,research,data-model,quickstart}.md`,
  `contracts/path-and-shell-contract.md`, `checklists/requirements.md`, `tasks.md`
  (19 tasks).
- Fixed `resolve_safe_path` in `py_mono/utils/path_utils.py`: replaced the string-prefix
  check with real path containment (`Path.is_relative_to`), checked against
  `WORKSPACE_ROOT` plus a new, empty-by-default `ADDITIONAL_ALLOWED_PATHS` allowlist
  (`py_mono/config.py`) — fixes all four existing file-tool callers with no per-tool
  changes.
- Gated the shell tool behind a new `ENABLE_SHELL_TOOL` opt-in (default false) via an
  extracted, testable `build_base_tools()` in `py_mono/main.py`; added a 30s subprocess
  timeout and corrected the tool's description to state plainly it's a best-effort
  blocklist, not a sandbox (`py_mono/tools/shell.py`).
- Changed `docker-compose.yml`'s `.:/app` mount to read-only, added the two new env vars
  there and to `.env.example`.
- Corrected `docs/adr/ADR-001-safe-execution-of-tools.md`'s claims to match the fixed,
  real behavior; Status `Proposed` → `Accepted`.
- Added `tests/utils/test_path_utils.py` (9 cases, 1 skipped on `win32`) and
  `tests/tools/test_shell.py` (16 cases).

**Files changed**: See commits `71a9ffa` (issue + Spec Kit artifacts), `ad8eb20`
(implementation) on branch `fix-workspace-sandbox`. Also this commit's session-doc updates.

**Design decisions**:
- Both original bugs were live-demonstrated against the real, pre-fix code during planning
  (not just read about) — `resolve_safe_path('../workspace_evil')` was confirmed to
  incorrectly accept a sibling-directory escape, and the shell tool was confirmed to run
  `ls /` and `cat /etc/os-release` with zero restriction. This grounded every design
  decision in observed, not assumed, behavior.
- Explicit user sign-off obtained on the one real behavior change: shell disabled by
  default rather than hardened-but-left-on, after walking through the trade-off directly
  (the user confirmed they'll set `ENABLE_SHELL_TOOL=true` themselves and specifically
  wanted confirmation that enabling it doesn't reduce its reach vs. today).
- Added `ADDITIONAL_ALLOWED_PATHS` at the user's explicit request, mid-session, as a
  deliberate, empty-by-default escape hatch — distinguishes "access granted on purpose"
  from the accidental access the original bug provided.
- `build_base_tools(enable_shell: Optional[bool] = None)` chosen over
  `importlib.reload()`-based env-var testing for `main.py`'s tool assembly — simpler and
  avoids module-reload fragility, at the cost of one extra parameter.

**Validation**:
- `python -m compileall -q py_mono` — exit 0.
- `pytest` (full suite, excluding the pre-existing broken `test_listallpy_skill.py`
  collection) — 71 passed, 1 skipped (Windows symlink test, real coverage lives in the
  Linux container), 2 pre-existing failures (`ISS-005`, confirmed unaffected), 0
  regressions.
- Real, non-mocked verification inside the actual running container (rebuilt with the new
  mount): the audit's own literal probe now correctly raises; `shell` confirmed absent by
  default and present with `ENABLE_SHELL_TOOL=true`; a `sleep 60` command was terminated at
  exactly 30.0s with the timeout message; `ls /` and `cat /etc/os-release` still succeed
  with shell enabled (reach genuinely unchanged, not narrowed); writes to `/workspace`,
  `/app/dynamic_tools`, `/app/skills` all still succeed and `uv pip install --system` still
  works; a direct write to `/app/py_mono/...` now fails with
  `[Errno 30] Read-only file system` (confirming the mount fix actually took effect).

**Open items**:
- ISS-003 (skills/dynamic tools executing code before approval) — untouched, deliberately
  out of scope for this branch, a distinct issue.
- ISS-005, ISS-006 — pre-existing, unrelated, not fixed here.
- Branch `fix-workspace-sandbox` has not been pushed or opened as a PR — left ready locally.

**Next safe action**: Review the `fix-workspace-sandbox` branch's 2 commits (plus this
session-doc commit), then push and open a PR into `main` when ready. With C-01/C-02 both
now addressed, ISS-003 (C-03) is the last of the original three critical audit findings.

---

## 2026-08-03 — Fix skill/dynamic-tool approval gate (ISS-003)
**Issue**: ISS-003

**Scope completed**:
- Registered/updated `ISS-003`, ran the fourth full Spec Kit cycle (4 user stories):
  `specs/004-fix-skill-tool-approval-gate/{spec,plan,research,data-model,quickstart}.md`,
  `contracts/approval-gate-contract.md`, `checklists/requirements.md`, `tasks.md` (25 tasks).
- Added `py_mono/skill/approval_ledger.py`: a new, separately-tracked approval ledger
  (`skills/.approvals.json`) recording a content hash of each approved skill's `skill.py`.
- `SkillRegistry.load()`/`reload_skill()` (`py_mono/skill/base.py`) now only `exec_module`
  a skill when `status: approved` AND the ledger's hash matches current content — editing
  `skill.py` after approval invalidates it until re-approved. `list_skills()` corrected so
  a proposed/hash-mismatched skill with real code is reported accurately.
- One-time auto-seed: the 8 pre-existing approved skills got ledger entries written
  automatically on first run, explicitly logged as seed events, not reviews — zero
  disruption.
- `Agent._handle_skill_approve()` (`py_mono/agent/agent.py`) now re-validates the current
  `skill.py` via `validate_skill_py()` before writing status/ledger — rejects outright if
  it contains a known-unsafe pattern.
- Added `ENABLE_DYNAMIC_TOOLS` (default false, `py_mono/config.py`), gated at both call
  sites (`py_mono/main.py`, `agent.py`'s `_reload_dynamic_tools()`) — mirrors ISS-002's
  `ENABLE_SHELL_TOOL` pattern exactly.
- `load_dynamic_tools()` (`py_mono/tools/tool_loader.py`) and `create_tool()`
  (`py_mono/tools/create_tool.py`) both run a new shared static safety check (forbidden
  pattern + AST syntax validation) before `exec_module`/before writing to disk —
  extracted `check_forbidden_patterns()` from `validator.py` as the single canonical
  source, imported by both.
- Corrected `docs/adr/ADR-013-Skill-Approval-and-Chaining.md` with an implementation-notes
  section — the stated policy was already correct, the code just didn't enforce it.
- Added `tests/test_skill_load_gating.py` (11 cases), `tests/tools/test_tool_loader.py`
  (7 cases), and 2 new cases in `tests/tools/test_create_tool.py`.

**Files changed**: See commits `d4cddfa` (issue + Spec Kit artifacts), `f542ccc`
(implementation) on branch `fix-skill-tool-approval-gate`. Also this commit's session-doc
updates.

**Design decisions**:
- The core bug was live-demonstrated against real, pre-fix code *before* any design work
  began (a throwaway proposed skill with a module-level `print`, loaded via a real
  `SkillRegistry` — the print fired immediately, confirming the audit's claim directly).
  The same reproduction was re-run post-fix, inside the real container, to close the loop.
- Explicit sign-off obtained on two real trade-offs before implementation: (1) a
  content-hash ledger with auto-seeding, over a simpler status-only gate — chosen because
  it also closes the "edit code and flip status together" tamper vector and gives the
  separate M-01 finding (no approval audit trail) a side-effect fix; (2) dynamic tools
  off by default via `ENABLE_DYNAMIC_TOOLS`, over static-validation-only — chosen because
  it's the only option that actually matches the audit's "disable... until isolated
  execution exists" recommendation, at the cost of the user's 5 existing local
  `dynamic_tools/*.py` files needing one opt-in to keep working (same trade-off already
  accepted for shell in ISS-002).
- `SafeAgentTools`/`run_skill_safe` (invocation-time tool-access constraints) deliberately
  left untouched — confirmed orthogonal, since they only apply to an already-approved,
  already-loaded skill's `run()` call, not to whether its module code executes at all.
- Discovered and fixed a real inconsistency while implementing: `_handle_skill_approve`
  used the module-level `SKILLS_DIR` constant for file paths but needed
  `self.skill_registry.skills_dir` for the ledger to support test isolation — fixed both
  paths to consistently use the registry's own `skills_dir`, removing the now-unused
  `SKILLS_DIR` import from `agent.py`.

**Validation**:
- `python -m compileall -q py_mono` — exit 0.
- `pytest` (full suite, excluding the pre-existing broken `test_listallpy_skill.py`
  collection) — 90 passed, 1 skipped (Windows symlink test, pre-existing convention from
  ISS-002), 2 pre-existing failures (`ISS-005`, confirmed unaffected), 0 regressions.
- Real, non-mocked verification inside the actual rebuilt container: the exact
  originally-demonstrated bug reproduced and confirmed fixed (marker does not fire for a
  proposed skill, does fire once approved); all 8 real skills auto-seeded and still load
  (`skills/.approvals.json` now tracked with 8 `seeded: true` entries); `/approve`'s real
  path (via `Agent._handle_skill_approve`, not mocked) rejects unsafe code and approves
  clean code; editing an approved skill post-approval reverts it to not-loaded; the real
  `dynamic_tools/` directory (6 files) loads 0 by default and the same 3 (of 6) with
  `ENABLE_DYNAMIC_TOOLS=true` as pre-fix (confirmed via `git stash` comparison — the other
  3 don't produce `Tool` instances for pre-existing, unrelated reasons, not new rejections
  from the static validation).

**Open items**:
- `ISS-008` (full isolated-worker-with-RPC execution) — newly logged, explicitly deferred,
  not started; the materially larger infrastructure item the audit's C-03 recommendation
  also called for.
- `ISS-005`, `ISS-006` — pre-existing, unrelated, not fixed here.
- Branch `fix-skill-tool-approval-gate` has not been pushed or opened as a PR — left ready
  locally.

**Next safe action**: Review the `fix-skill-tool-approval-gate` branch's 2 commits (plus
this session-doc commit), then push and open a PR into `main` when ready. With C-01, C-02,
and C-03 all now addressed, all three original critical audit findings are resolved —
remaining tracked work is `ISS-005`, `ISS-006` (both minor/pre-existing), and `ISS-008`
(the deferred isolation project).
still open.

---

## 2026-08-30 -- M7 kickoff and first lifecycle slice specification
**Issue**: ISS-015 (Add first skill lifecycle graph slice)

**Scope completed**:
- Confirmed that `docs/ISSUES.md` and `docs/ROADMAP_PLAN.md` superseded stale status docs:
  M6 is complete and M7 is the next product milestone.
- Updated `docs/PROJECT_STATUS.md`, `docs/CURRENT_FOCUS.md`, and `docs/NEXT_ACTIONS.md` to
  reflect M6 completion and M7 kickoff.
- Updated `docs/ROADMAP_PLAN.md` so M7 no longer reads as not started.
- Promoted the first M7 slice into `docs/ISSUES.md` as `ISS-015`.
- Ran Spec Kit specify, plan, and tasks for the first M7 slice:
  `Critique -> Generate -> Validate -> Test(smoke run) -> Propose`.
- Created the specification quality checklist and marked it complete after review.
- Added `plan.md`, `research.md`, `data-model.md`, `contracts/skill-lifecycle-output.md`,
  `quickstart.md`, and `tasks.md` for implementation handoff.

**Files changed**:
- `docs/PROJECT_STATUS.md`
- `docs/CURRENT_FOCUS.md`
- `docs/NEXT_ACTIONS.md`
- `docs/ISSUES.md`
- `docs/ROADMAP_PLAN.md`
- `.specify/feature.json`
- `specs/013-skill-lifecycle-smoke-test/spec.md`
- `specs/013-skill-lifecycle-smoke-test/checklists/requirements.md`
- `specs/013-skill-lifecycle-smoke-test/plan.md`
- `specs/013-skill-lifecycle-smoke-test/research.md`
- `specs/013-skill-lifecycle-smoke-test/data-model.md`
- `specs/013-skill-lifecycle-smoke-test/contracts/skill-lifecycle-output.md`
- `specs/013-skill-lifecycle-smoke-test/quickstart.md`
- `specs/013-skill-lifecycle-smoke-test/tasks.md`
- `docs/SESSION_LOG.md`

**Design decisions**:
- Kept `ISS-015` narrow: critique, generation, existing validation, one synthetic smoke run, and
  proposed-state surfacing only.
- Left diff-on-regeneration and production failure-driven evolution for later M7 issues.
- Left `ISS-008` isolated-worker execution gated/deferred and did not mix it into M7's first
  product slice.
- Preserved the existing approval hash-ledger boundary as the authority for runnable skills.

**Validation**:
- Reviewed the new spec against the Spec Kit quality checklist: all checklist items passed.
- Reviewed the generated plan/tasks against the project constitution; no violations recorded.
- No production code changed; automated tests were not run.

**Open items**:
- `ISS-015` is specified, planned, and task-broken-down, but not implemented.
- `ISS-008` remains open and gated as an M8 prerequisite.

**Next safe action**: Create an implementation branch for `ISS-015` and start `tasks.md` at
T001.

---

## 2026-08-30 -- Implement ISS-015 and plan next M7 slices
**Issue**: ISS-015 (Add first skill lifecycle graph slice), plus filing/planning `ISS-016` and
`ISS-017`

**Scope completed**:
- Created branch `implement-m7-skill-lifecycle`.
- Implemented `ISS-015`: `generate_skill` now reports Critique, Generate, Validate, Test, and
  Propose lifecycle stages.
- Added pre-approval smoke testing for generated skill code after static validation and before
  proposal.
- Preserved the approval boundary: passing lifecycle checks leave the skill proposed and do not
  write approval ledger entries.
- Updated the approval ledger hash for the intentionally changed, already-approved
  `generate_skill` skill.
- Filed, specified, and planned `ISS-016` as the separate diff-on-regeneration M7 slice.
- Filed, specified, and planned `ISS-017` as the separate failure-driven evolution M7 slice.
- Kept lifecycle persistence/reporting and CLI/UX polish out of `ISS-016`/`ISS-017`, per user
  direction.

**Files changed**:
- `py_mono/skill/lifecycle.py`
- `skills/generate_skill/skill.py`
- `skills/.approvals.json`
- `tests/test_skill_lifecycle.py`
- `tests/test_generate_skill.py`
- `.specify/feature.json`
- `docs/PROJECT_STATUS.md`
- `docs/CURRENT_FOCUS.md`
- `docs/NEXT_ACTIONS.md`
- `docs/ISSUES.md`
- `docs/ROADMAP_PLAN.md`
- `docs/SESSION_LOG.md`
- `specs/013-skill-lifecycle-smoke-test/*`
- `specs/014-skill-regeneration-diff/*`
- `specs/015-failure-driven-skill-evolution/*`

**Design decisions**:
- Put lifecycle primitives in `py_mono/skill/lifecycle.py`, alongside validation, approval,
  telemetry, and fitness.
- Kept `generate_skill` as the user-facing lifecycle orchestrator.
- Smoke testing imports validated generated code from a temporary file and runs it once with safe
  tool wrappers; it does not use `SkillRegistry` and does not touch the approval ledger.
- `ISS-016` and `ISS-017` are planned only, not implemented, and remain separate from
  persistence/reporting and CLI/UX polish.

**Validation**:
- `uv run pytest tests/test_skill_lifecycle.py -v` — 6 passed.
- `uv run pytest tests/test_generate_skill.py -v` — 3 passed.
- `uv run pytest tests/test_skill_approval.py tests/test_generate_skill.py -v` — 13 passed.
- `uv run pytest -q` — 145 passed, 1 skipped.
- `uv run python -m compileall -q py_mono skills` — exit 0. The first sandboxed attempt hit a
  `uv` cache permission issue; rerun outside the sandbox completed successfully.

**Open items**:
- `ISS-016` is specified and planned, but not implemented.
- `ISS-017` is specified and planned, but not implemented.
- Persistence/reporting polish and CLI/UX polish still need separate issues when ready.
- `ISS-008` remains gated/deferred as an M8 prerequisite.

**Next safe action**: Review the M7 split and decide whether to implement `ISS-016` next on
`implement-m7-skill-lifecycle` or split it into its own branch.

---

## 2026-08-30 -- Implement ISS-016 and ISS-017
**Issue**: `ISS-016` (Show diff when regenerating an existing skill) and `ISS-017` (Propose skill
revisions from failure context)

**Scope completed**:
- Implemented `ISS-016`: generation for an existing skill now produces a `.candidate` proposal,
  renders separate `SKILL.md` and `skill.py` diffs against the approved baseline when available,
  and reports missing baselines explicitly.
- Updated `/approve <skill>` to validate and promote `.candidate` proposals through the existing
  approval flow; invalid candidates are rejected without overwriting the approved skill.
- Implemented `ISS-017`: `/skill generate_skill --evolve <skill-name>` now reads the latest
  actionable failed telemetry record, includes that failure context in generation, reuses the
  lifecycle checks, and saves the output as a candidate proposal.
- Extended telemetry minimally with optional `request` and `failure_reason` fields populated by
  `run_skill_safe` on failures.
- Fixed registry path resolution so hyphenated on-disk skill directories still work with
  normalized internal skill names and approval-ledger checks.
- Kept persistence/reporting and CLI/UX polish separate, per user direction.

**Files changed**:
- `py_mono/skill/diffing.py`
- `py_mono/skill/evolution.py`
- `py_mono/skill/telemetry.py`
- `py_mono/skill/approval.py`
- `py_mono/skill/base.py`
- `py_mono/agent/agent.py`
- `skills/generate_skill/skill.py`
- `skills/.approvals.json`
- `tests/test_skill_diffing.py`
- `tests/test_skill_evolution.py`
- `tests/test_generate_skill.py`
- `tests/test_skill_telemetry.py`
- `tests/test_skill_approval.py`
- `docs/PROJECT_STATUS.md`
- `docs/CURRENT_FOCUS.md`
- `docs/NEXT_ACTIONS.md`
- `docs/ISSUES.md`
- `docs/ROADMAP_PLAN.md`
- `docs/SESSION_LOG.md`

**Design decisions**:
- Regenerated and evolved outputs are stored under `skills/<name>/.candidate/` so the approved
  skill remains in place until explicit approval.
- `/approve` is the only promotion path; it validates candidate code before replacing current
  files and writing the approval ledger.
- Failure-driven evolution reuses the `ISS-015` lifecycle and the `ISS-016` candidate/diff path
  instead of creating a separate self-patching path.
- Telemetry was extended in the existing JSONL stream rather than adding a second persistence
  mechanism.

**Validation**:
- `uv run pytest tests/test_generate_skill.py tests/test_skill_diffing.py tests/test_skill_evolution.py -v`
  — 19 passed.
- `uv run pytest tests/test_skill_telemetry.py tests/test_skill_approval.py tests/test_skill_load_gating.py -v`
  — 26 passed.
- `uv run pytest -q` — 162 passed, 1 skipped.
- `uv run python -m compileall -q py_mono skills` — exit 0 after rerun outside the sandbox due
  the same `uv` cache permission issue seen earlier.

**Open items**:
- Persistence/reporting polish for lifecycle state still needs a separate issue if wanted.
- CLI/UX polish for lifecycle output still needs a separate issue if wanted.
- `ISS-008` remains open and gated as an M8 prerequisite.

**Next safe action**: Review branch `implement-m7-skill-lifecycle`, then commit and merge if
accepted.

---

## 2026-08-30 -- Record M7 closeout split before merge
**Issue**: M7 closeout planning (`ISS-018`, `ISS-019`) plus branch handoff for M7 core work

**Scope completed**:
- Filed `ISS-018` as the M7 closeout issue for persisting and reporting skill lifecycle state.
- Filed `ISS-019` as the M7 closeout issue for CLI/UX polish around lifecycle review.
- Recorded the intended order: `ISS-018` first, `ISS-019` second, revisit `ISS-008`, then start
  M8.
- Updated status, focus, roadmap, and next-action docs to reflect that `ISS-015`, `ISS-016`, and
  `ISS-017` are M7 core complete while `ISS-018` and `ISS-019` remain open closeout work.

**Files changed**:
- `docs/ISSUES.md`
- `docs/PROJECT_STATUS.md`
- `docs/CURRENT_FOCUS.md`
- `docs/NEXT_ACTIONS.md`
- `docs/ROADMAP_PLAN.md`
- `docs/SESSION_LOG.md`

**Design decisions**:
- Kept lifecycle persistence/reporting separate from CLI polish because the CLI needs stable
  persisted state to display.
- Kept both items before M8 so provenance/sharing work does not start on top of unclear lifecycle
  review state.
- Left `ISS-008` as the explicit M8 prerequisite to revisit after M7 closeout.

**Validation**:
- Pending in this entry; run `git diff --check` and the existing test/compile validation before
  committing the branch.

**Open items**:
- `ISS-018` is filed but not specified, planned, or implemented.
- `ISS-019` is filed but not specified, planned, or implemented.
- `ISS-008` remains open and gated as an M8 prerequisite.

**Next safe action**: Commit and merge `implement-m7-skill-lifecycle`; next feature work should
start with Spec Kit for `ISS-018`.

---

## 2026-08-31 -- Implement ISS-018 lifecycle state reports
**Issue**: `ISS-018` (Persist and report skill lifecycle state)

**Scope completed**:
- Created the Spec Kit artifacts for `ISS-018` under `specs/016-lifecycle-state-reports/`.
- Added durable lifecycle report persistence for generated, regenerated, evolved, and failed
  skill candidate attempts.
- Reports are written as both Markdown and JSON next to proposed artifacts:
  `skills/<name>/lifecycle_report.{md,json}` for new skill proposals and
  `skills/<name>/.candidate/lifecycle_report.{md,json}` for regeneration/evolution proposals.
- Reports include lifecycle stage results, smoke-test request/output/failure details, baseline
  availability, rendered diffs, evolution failure context, and review/approval next steps.
- Preserved the approval boundary: report writing does not approve, load, or execute proposed
  skills.
- Updated candidate promotion so approving a regeneration/evolution candidate preserves the
  lifecycle report at the skill root while removing `.candidate/` as before.
- Updated the `generate_skill` approval-ledger hash for the intentional implementation change.

**Files changed**:
- `.specify/feature.json`
- `py_mono/skill/reporting.py`
- `py_mono/skill/diffing.py`
- `skills/generate_skill/skill.py`
- `skills/.approvals.json`
- `tests/test_skill_lifecycle_reporting.py`
- `tests/test_generate_skill.py`
- `README.md`
- `docs/ISSUES.md`
- `docs/PROJECT_STATUS.md`
- `docs/CURRENT_FOCUS.md`
- `docs/NEXT_ACTIONS.md`
- `docs/ROADMAP_PLAN.md`
- `docs/SESSION_LOG.md`
- `specs/016-lifecycle-state-reports/*`

**Design decisions**:
- Stored reports beside the candidate artifacts because that is already the review surface.
- Wrote Markdown for human inspection and JSON as a stable structured source for `ISS-019` CLI
  polish.
- Treated report write failures as visible warnings, not candidate validation failures, so report
  persistence cannot corrupt or approve skill artifacts.
- Kept historical report indexing and dashboards out of scope.

**Validation**:
- `uv run pytest -q tests/test_skill_lifecycle_reporting.py tests/test_generate_skill.py` --
  12 passed.
- `uv run pytest -q` -- 165 passed, 1 skipped.
- `uv run python -m compileall -q py_mono skills` -- exit 0. The first sandboxed compile attempt
  hit the known uv cache permission issue; rerun outside the sandbox completed successfully.

**Open items**:
- `ISS-019` remains open for CLI/UX polish around lifecycle review.
- `ISS-008` remains open as the real isolated-worker execution prerequisite before M8.

**Next safe action**: Commit and merge `iss-018-lifecycle-reports`, then create an `ISS-019`
branch from `main` and start CLI review polish using the new report JSON as the stable display
source.
