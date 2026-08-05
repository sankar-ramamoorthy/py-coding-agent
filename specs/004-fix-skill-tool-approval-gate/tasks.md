---

description: "Task list for fixing the skill/dynamic-tool approval gate (ISS-003)"
---

# Tasks: Fix Skill/Tool Approval Gate

**Input**: Design documents from `/specs/004-fix-skill-tool-approval-gate/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/approval-gate-contract.md, quickstart.md

**Tests**: Included — Constitution Principle IV requires test coverage for new behavior.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md). No new
directories are needed (`tests/tools/` already exists; new test files land flat at
`tests/` root, matching the existing convention) — no separate Setup phase.

## Path Conventions

All paths relative to the repository root. `py_mono/skill/base.py`, `py_mono/skill/validator.py`,
`py_mono/agent/agent.py`, `py_mono/config.py`, `py_mono/main.py`,
`py_mono/tools/tool_loader.py`, `py_mono/tools/create_tool.py`, and
`docs/adr/ADR-013-*.md` are existing files being modified. `py_mono/skill/approval_ledger.py`
and `skills/.approvals.json` are new.

---

## Phase 1: Foundational (Blocking Prerequisites)

**Purpose**: The approval-ledger module and shared validation source both US1/US2 (skills)
and US3/US4 (dynamic tools) build on.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T001 Create `py_mono/skill/approval_ledger.py`: `load_ledger(path) -> dict`,
      `save_ledger(path, ledger)`, `hash_file(path) -> str` (sha256 hex digest),
      `is_approved(ledger, skill_name, skill_py_path) -> bool` (status check happens at the
      call site; this just compares current hash to ledger entry), `record_approval(ledger,
      skill_name, skill_py_path, seeded=False)`. Ledger path defaults to
      `skills/.approvals.json`.
- [X] T002 [P] Export `FORBIDDEN_PATTERNS` from `py_mono/skill/validator.py` for reuse
      (confirm it's already a module-level name; add `__all__` or leave as-is if already
      importable — no functional change, just confirming the shared-source decision from
      `research.md`)
- [X] T003 [P] Add `ENABLE_DYNAMIC_TOOLS` (truthy-string-parsed, default `False`) to
      `py_mono/config.py`, with a doc-comment block matching `ENABLE_SHELL_TOOL`'s style

**Checkpoint**: Ledger module and shared validation source exist — user story
implementation can begin

---

## Phase 2: User Story 1 - A proposed skill's code never runs before approval (Priority: P1) 🎯 MVP

**Goal**: `SkillRegistry.load()`/`reload_skill()` only execute a skill's code when it's
approved AND the ledger's hash matches current content; metadata stays inspectable either way.

**Independent Test**: A not-yet-approved skill with an observable module-level side effect
— confirm the side effect never fires on `load()`, and the skill is still listed.

### Tests for User Story 1 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T006 doesn't exist yet)

- [X] T004 [P] [US1] Write `tests/test_skill_load_gating.py`: a `tmp_path`-based
      `SkillRegistry` fixture (mirrors this session's live demo) — a `status: proposed`
      skill's module-level marker does NOT fire on `load()`, and `list_skills()` still
      reports its name/description/status; a `status: approved` skill WITH a matching
      ledger entry DOES fire, exactly once

### Implementation for User Story 1

- [X] T005 [US1] In `py_mono/skill/base.py`, gate the existing `_load_skill_py()` call in
      `load()` and `reload_skill()` on `status == "approved"` AND
      `approval_ledger.is_approved(ledger, name, skill_py)` (depends on T001) — metadata
      parsing (`_parse_skill_md`) is untouched, always runs
- [X] T006 [US1] Adjust `list_skills()` in `py_mono/skill/base.py` so a skill with real
      code that isn't currently loaded (proposed, or hash-mismatched) is reported
      accurately (has code, not currently active) rather than misreported as spec-only
- [X] T007 [US1] Run `pytest tests/test_skill_load_gating.py -v` and confirm T004's US1
      cases pass

**Checkpoint**: User Story 1 is fully functional and independently testable — the core
demonstrated bug is fixed (FR-001, FR-002, SC-001).

---

## Phase 3: User Story 2 - Approval re-validates and expires on later changes (Priority: P2)

**Goal**: `/approve` re-checks current `skill.py` before writing the ledger; a later edit
invalidates approval until renewed; the 8 already-approved skills are unaffected.

**Independent Test**: Approving unsafe content is refused; approving clean content
succeeds and enables execution; editing after approval reverts to not-loaded.

### Tests for User Story 2 ⚠️

- [X] T008 [US2] Add cases to `tests/test_skill_load_gating.py`: `/approve`-equivalent
      (calling `_handle_skill_approve` or the underlying validation+ledger-write logic
      directly) refuses a skill.py containing a forbidden pattern — SKILL.md and ledger
      both untouched, marker never fires; succeeds for clean code — SKILL.md flips,
      ledger entry written, THEN the marker fires; editing `skill.py` after approval and
      calling `reload_skill()` again reverts to not-loaded (hash mismatch)
- [X] T009 [US2] Add a regression test: load the real `skills/` directory via
      `SkillRegistry(skills_dir=SKILLS_DIR).load()`, confirm all 8 real skills
      (`hello`, `generate_skill`, `scaffold_project`, `bug_fix`, `generate_playbook`,
      `doc_sync`, `create_skill_py`, `refactor_extract_function`) load successfully and
      `skills/.approvals.json` gets `seeded: true` entries for each

### Implementation for User Story 2

- [X] T010 [US2] In `py_mono/agent/agent.py::_handle_skill_approve()`: read current
      `skill.py`, call `validate_skill_py()` — reject (leave SKILL.md/ledger untouched,
      return the failure reason) if invalid; on success, write `status: approved`, call
      `approval_ledger.record_approval(...)` with `seeded=False`, then `reload_skill()`
      as today (depends on T001, T005)
- [X] T011 [US2] In `py_mono/skill/base.py`'s `load()` (or a dedicated `_seed_ledger()`
      helper called from it): for each skill with `status == "approved"` and no ledger
      entry, call `approval_ledger.record_approval(..., seeded=True)` and log an explicit
      "auto-seeded, not reviewed" message, before the load-gate check runs for that skill
      so it loads on this same call (depends on T001, T005)
- [X] T012 [US2] Run `pytest tests/test_skill_load_gating.py -v` and confirm all US2 cases
      (T008, T009) pass

**Checkpoint**: User Stories 1 AND 2 both work independently — approval is re-validated
and tamper-evident, existing skills are unaffected (FR-003 through FR-006, SC-002 through SC-004).

---

## Phase 4: User Story 3 - Auto-generated tools default to not running automatically (Priority: P3)

**Goal**: Dynamic tools don't load unless `ENABLE_DYNAMIC_TOOLS` is explicitly set.

**Independent Test**: Default state — no dynamic tools load. Explicitly enabled — they load
exactly as today.

### Tests for User Story 3 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T014 doesn't exist yet)

- [X] T013 [P] [US3] Write `tests/tools/test_tool_loader.py`: with `ENABLE_DYNAMIC_TOOLS`
      unset/false, the gated call sites produce zero dynamic tools; with it true, a valid
      dynamic tool file loads exactly as today (use a `tmp_path` dynamic-tools folder, no
      real network/filesystem dependency on the repo's own `dynamic_tools/`)

### Implementation for User Story 3

- [X] T014 [US3] In `py_mono/main.py::main()` and `py_mono/agent/agent.py::_reload_dynamic_tools()`,
      check `ENABLE_DYNAMIC_TOOLS` (depends on T003) before calling `load_dynamic_tools()`
      at all — when false, treat as zero dynamic tools; `/reload_tools`'s response
      explains the capability is disabled rather than silently loading nothing
- [X] T015 [US3] Run `pytest tests/tools/test_tool_loader.py -v` and confirm the T013
      gating cases pass

**Checkpoint**: User Stories 1, 2, AND 3 all work independently — dynamic tools are
off by default (FR-007, SC-005).

---

## Phase 5: User Story 4 - Generated tool code is safety-checked before it can exist (Priority: P4)

**Goal**: Static validation runs on every dynamic-tool file before `exec_module`, and on
`create_tool()`'s LLM-supplied code before it's ever written to disk.

**Independent Test**: A forbidden-pattern file is skipped at load time and refused at
creation time; clean code works exactly as today in both places.

### Tests for User Story 4 ⚠️

- [X] T016 [US4] Add cases to `tests/tools/test_tool_loader.py`: a `tmp_path` dynamic-tools
      file containing a forbidden pattern is skipped (logged, not raised) even with
      `ENABLE_DYNAMIC_TOOLS=true`; a clean file still loads
- [X] T017 [US4] Add cases to `tests/tools/test_create_tool.py` (new assertions only, not
      touching the existing ISS-005-flagged failing ones): `create_tool()` with
      forbidden-pattern code writes no file and returns an error string; clean code still
      writes successfully

### Implementation for User Story 4

- [X] T018 [US4] In `py_mono/tools/tool_loader.py::load_dynamic_tools()`, before
      `exec_module`, run the shared forbidden-pattern/AST check (depends on T002) against
      each file's text; skip (log a warning) any file that fails
- [X] T019 [US4] In `py_mono/tools/create_tool.py::create_tool()`, before
      `path.write_text(wrapped_code, ...)`, run the same validator against `code`; return
      an error string and write nothing if invalid (depends on T002)
- [X] T020 [US4] Run `pytest tests/tools/test_tool_loader.py tests/tools/test_create_tool.py -v`
      and confirm all T016/T017 cases pass

**Checkpoint**: All four user stories are independently functional (FR-008, SC-006).

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T021 [P] Add an "Implementation Notes: corrected 2026-08-03" section to
      `docs/adr/ADR-013-*.md` pointing at this feature, mirroring ADR-001's correction in
      ISS-002
- [X] T022 Run `python -m compileall -q py_mono` — repo-wide syntax gate
- [X] T023 Run `pytest` (full suite) at the repo root — confirm nothing existing
      regressed, the two pre-existing `ISS-005` failures remain exactly as documented
- [X] T024 Real, non-mocked verification, inside the actual rebuilt container — all
      confirmed: the original live-demo skill (proposed, module-level marker) does NOT
      execute at `load()`; the same skill, approved with a matching ledger entry, DOES
      execute exactly once; all 8 real skills in `skills/` auto-seeded and still load
      (confirmed via `skills/.approvals.json`, now tracked); `/approve`'s real path
      rejects forbidden-pattern code and succeeds for clean code (via `Agent._handle_skill_approve`
      directly, not mocked); editing an approved skill's `skill.py` post-approval reverts
      it to not-loaded; the real `dynamic_tools/` directory's files load zero by default
      and the same 3 (of 6) load when `ENABLE_DYNAMIC_TOOLS=true` — confirmed identical to
      pre-fix behavior via `git stash` comparison, so the other 3 not loading is
      pre-existing and unrelated, not a regression from the new static validation
- [ ] T025 Update `docs/ISSUES.md` (mark `ISS-003` done, log new `ISS-008` for the
      deferred isolated-worker-with-RPC item), and fill in `docs/SESSION_LOG.md`,
      `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md` with the real end-of-session state
      per AGENTS.md's Session Completion section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Foundational (Phase 1)**: No dependencies — BLOCKS all user stories
- **User Story 1 (Phase 2)**: Depends on Foundational (T001, ledger module)
- **User Story 2 (Phase 3)**: Depends on User Story 1 (T005 — the gate `/approve` writes
  into) and Foundational (T001)
- **User Story 3 (Phase 4)**: Depends on Foundational (T003) only — independent of US1/US2
- **User Story 4 (Phase 5)**: Depends on Foundational (T002) only — independent of
  US1/US2/US3, though T018/T019 land in the same files US3 touches (T014), so sequence
  them after US3 to avoid overlapping edits to `tool_loader.py`
- **Polish (Phase 6)**: Depends on all four user stories being complete

### Parallel Opportunities

- T002, T003 (Foundational) can run in parallel with T001 (different files)
- T013 (US3 tests) can be written in parallel with T004 (US1 tests) — different files, no
  shared dependency beyond their respective Foundational pieces
- T021 (ADR correction) can proceed in parallel with T022–T024 (different file)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundational (ledger module, shared validation source, new env var)
2. Complete Phase 2: User Story 1 — the concretely demonstrated bug is fixed
3. **STOP and VALIDATE**: reproduce the live demo for real, confirm the marker no longer fires

### Incremental Delivery

1. Foundational → ledger module and shared validation source ready
2. Add User Story 1 → core bug fixed (MVP)
3. Add User Story 2 → approval is re-validated and tamper-evident, existing skills safe
4. Add User Story 3 → dynamic tools off by default
5. Add User Story 4 → static validation closes the "write unvalidated code" gap
6. Polish → ADR correction, repo-wide regression checks, real end-to-end proof

---

## Notes

- [P] tasks touch different files with no dependency on an incomplete task
- Tests (T004, T008, T009, T013, T016, T017) are written before their corresponding
  implementation per Constitution Principle IV
- Commit after each phase completes, split roughly as: Foundational (ledger + config),
  US1+US2 (skills gate + approve re-validation + auto-seed), US3+US4 (dynamic tools gate +
  static validation), then ADR + session-doc updates last
