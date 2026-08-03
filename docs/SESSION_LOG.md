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
- kb-template/ repo split, TradeForge-KnowledgeBase/AITrader migration onto this schema,
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
