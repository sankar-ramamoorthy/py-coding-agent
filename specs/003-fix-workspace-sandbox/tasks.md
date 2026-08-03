---

description: "Task list for fixing the workspace sandbox escape (ISS-002)"
---

# Tasks: Fix Workspace Sandbox Escape

**Input**: Design documents from `/specs/003-fix-workspace-sandbox/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md,
contracts/path-and-shell-contract.md, quickstart.md

**Tests**: Included — Constitution Principle IV requires test coverage for new behavior.

**Organization**: Tasks are grouped by user story (US1–US4 from spec.md).

## Path Conventions

All paths relative to the repository root. `py_mono/utils/path_utils.py`,
`py_mono/config.py`, `py_mono/tools/shell.py`, `py_mono/main.py`, `docker-compose.yml`,
`.env.example`, and `docs/adr/ADR-001-safe-execution-of-tools.md` are existing files being
modified. `tests/utils/` is a new top-level test directory (`tests/tools/` already exists).

---

## Phase 1: Setup

- [ ] T001 Create `tests/utils/` directory

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: New config surface needed by US1/US2 (path allowlist) and US3 (shell gating).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Add `ENABLE_SHELL_TOOL` (truthy-string-parsed, default `False`) and
      `ADDITIONAL_ALLOWED_PATHS` (comma-separated env var parsed into a list of
      `.resolve()`'d `Path` objects, default empty) to `py_mono/config.py`, with doc-comment
      blocks explaining both per `data-model.md`

**Checkpoint**: Config surface exists — user story implementation can begin

---

## Phase 3: User Story 1 - A path outside the workspace is always rejected (Priority: P1) 🎯 MVP

**Goal**: Real path containment replaces the string-prefix check; sibling-prefix,
traversal, and symlink escapes are all rejected; genuine in-workspace access is unaffected.

**Independent Test**: Attempt a sibling-prefix-collision path, `../` traversal, and a
symlink escape — all rejected. Attempt a genuine in-workspace path — still accepted.

### Tests for User Story 1 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T005 doesn't exist yet)

- [ ] T003 [P] [US1] Write `tests/utils/test_path_utils.py`: valid in-workspace path still
      resolves; `../` traversal rejected; sibling-prefix collision rejected (reproduces the
      audit's own `/workspace_evil` probe, live-confirmed during planning to currently
      *pass* incorrectly); absolute-path escape rejected; symlink escape rejected — skipped
      on `win32` (`@pytest.mark.skipif(sys.platform == "win32", ...)`, symlink creation
      needs Developer Mode/elevation not guaranteed in this dev environment)

### Implementation for User Story 1

- [ ] T004 [US1] Fix `resolve_safe_path` in `py_mono/utils/path_utils.py`: replace
      `str.startswith` with `path.is_relative_to(root)` checked against
      `allowed_roots = [WORKSPACE_ROOT] + ADDITIONAL_ALLOWED_PATHS` (depends on T002).
      Fixes all four existing callers (`read_file.py`, `write_file.py`, `edit_file.py`,
      `list_files.py`) with no per-tool changes.
- [ ] T005 [US1] Run `pytest tests/utils/test_path_utils.py -v` and confirm all US1 cases
      from T003 pass

**Checkpoint**: User Story 1 is fully functional and independently testable — real path
containment works (FR-001 through FR-004, SC-001).

---

## Phase 4: User Story 2 - Deliberately grant access to specific additional directories (Priority: P2)

**Goal**: An operator-configured allowlist of additional directories is checked alongside
the workspace; empty by default, so nothing changes until configured.

**Independent Test**: With no additional directories configured, behavior matches
workspace-only access. With one configured, a path inside it is accepted, a path outside
both is still rejected.

### Tests for User Story 2 ⚠️

- [ ] T006 [US2] Add additional-allowed-paths test cases to
      `tests/utils/test_path_utils.py`: a path inside a configured
      `ADDITIONAL_ALLOWED_PATHS` entry is accepted even though it's outside
      `WORKSPACE_ROOT`; a path outside both is still rejected; with the list empty (the
      default), behavior is identical to the workspace-only case (regression)

### Implementation for User Story 2

- [ ] T007 [US2] No new production code expected — `T004`'s `allowed_roots` list already
      incorporates `ADDITIONAL_ALLOWED_PATHS` from `T002`'s config addition. This task is
      verification only.
- [ ] T008 [US2] Run `pytest tests/utils/test_path_utils.py -v` and confirm all US2 cases
      from T006 pass

**Checkpoint**: User Stories 1 AND 2 both work independently — the allowlist mechanism
works and defaults to a no-op (FR-005, FR-006, SC-002).

---

## Phase 5: User Story 3 - Shell command execution is an explicit, trusted opt-in (Priority: P3)

**Goal**: Shell is absent from a default session's tools; explicit configuration is the
only way to enable it; an enabled shell command still times out; its description is honest;
its reach is otherwise unchanged.

**Independent Test**: A session with no special configuration has no shell capability.
Explicitly enabling it makes it available. An indefinitely-running command is terminated.

### Tests for User Story 3 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T010, T011 don't exist yet)

- [ ] T009 [P] [US3] Write `tests/tools/test_shell.py`: `ENABLE_SHELL_TOOL` defaults false,
      parses common truthy strings (`"1"`, `"true"`, `"yes"`, `"on"`, case-insensitive);
      `build_base_tools(enable_shell=...)` excludes/includes `"shell"` per the parameter
      (`None` reads the env var, explicit `True`/`False` overrides it); timeout is passed
      to `subprocess.run` (mocked, no real subprocess); existing blocklist behavior still
      works (regression test, not framed as a security guarantee)

### Implementation for User Story 3

- [ ] T010 [US3] Add `DEFAULT_SHELL_TIMEOUT_SECONDS = 30` to `py_mono/tools/shell.py`, pass
      `timeout=DEFAULT_SHELL_TIMEOUT_SECONDS` to `subprocess.run`, catch
      `subprocess.TimeoutExpired` **before** the generic `except Exception` (it's a
      subclass); update the `Tool(...)` description to state plainly this is a best-effort
      filter, not a content sandbox
- [ ] T011 [US3] Extract `build_base_tools(enable_shell: Optional[bool] = None) -> list` in
      `py_mono/main.py`, mirroring the existing `load_mcp_tools()`/`load_skills()`
      extraction pattern; gate `shell_tool`'s inclusion on the effective flag (depends on
      T002, T010); update `main()` to call it
- [ ] T012 [US3] Run `pytest tests/tools/test_shell.py -v` and confirm all US3 cases from
      T009 pass

**Checkpoint**: User Stories 1, 2, AND 3 all work independently — shell is opt-in, times
out, and its description is honest (FR-007 through FR-011, SC-003, SC-004).

---

## Phase 6: User Story 4 - The development container's source mount is no broader than necessary (Priority: P4)

**Goal**: `docker-compose.yml`'s full-repo mount becomes read-only; the three
runtime-writable subdirectories remain writable.

**Independent Test**: Inside the running container, the three writable subdirectories
still accept writes; a write attempt to the mounted source outside them fails.

### Implementation for User Story 4

- [ ] T013 [US4] Update `docker-compose.yml`: `.:/app` → `.:/app:ro`; add
      `ENABLE_SHELL_TOOL=${ENABLE_SHELL_TOOL:-false}` and
      `ADDITIONAL_ALLOWED_PATHS=${ADDITIONAL_ALLOWED_PATHS:-}` to the `environment:` block
- [ ] T014 [US4] Update `.env.example` with commented-out `ENABLE_SHELL_TOOL=true` and
      `ADDITIONAL_ALLOWED_PATHS=` (empty, with a comment showing comma-separated syntax)
      example lines

**Checkpoint**: All four user stories are independently functional. Real verification
(container rebuild, write-path checks) happens in Polish, since this story has no
meaningful unit-test surface (FR-012, SC-005).

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T015 [P] Update `docs/adr/ADR-001-safe-execution-of-tools.md` in place: Status
      `Proposed` → `Accepted`, add a superseded/corrected note dated 2026-08-03 pointing at
      this feature; correct the exception-vs-string claim (§1), the
      "cwd-prevents-system-wide-effects" implication (§3), and "no elevated privileges"
      (§6); add lines documenting `ADDITIONAL_ALLOWED_PATHS` and the now-read-only mount
- [ ] T016 Run `python -m compileall -q py_mono` — repo-wide syntax gate
- [ ] T017 Run `pytest` (full suite) at the repo root — confirm nothing existing regressed,
      the two pre-existing `ISS-005` failures remain exactly as documented
- [ ] T018 Real, non-mocked verification inside the actual Docker container: re-run the
      audit's own literal probe (`resolve_safe_path("../workspace_evil")` must now raise);
      confirm `shell` absent/present per `ENABLE_SHELL_TOOL`; confirm an indefinitely-running
      shell command times out at 30s; confirm shell's reach is otherwise unchanged (`ls /`,
      `cat /etc/os-release` still work when enabled — this fix doesn't narrow shell
      content); rebuild with the new mount and confirm the three writable subdirectories
      still accept writes while a write outside them now fails read-only
- [ ] T019 Update `docs/ISSUES.md` (mark `ISS-002` done), and fill in
      `docs/SESSION_LOG.md`, `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md` with the real
      end-of-session state per AGENTS.md's Session Completion section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T002, for `ADDITIONAL_ALLOWED_PATHS`
  to exist, even though US1 itself only exercises the `WORKSPACE_ROOT`-only case)
- **User Story 2 (Phase 4)**: Depends on User Story 1 (T004 — same function, same
  `allowed_roots` list)
- **User Story 3 (Phase 5)**: Depends on Foundational only (T002) — independent of US1/US2
- **User Story 4 (Phase 6)**: Independent of all other stories — pure infra/config change
- **Polish (Phase 7)**: Depends on all four user stories being complete

### Parallel Opportunities

- T003 (US1 tests) and T009 (US3 tests) can be written in parallel (different files, no
  shared dependency beyond T002)
- T013/T014 (US4) can proceed in parallel with US1/US2/US3 entirely — no code overlap
- T015 (ADR update) can proceed in parallel with T016–T018 (different file, no dependency)

---

## Parallel Example: after Foundational (T002) completes

```bash
Task: "Write tests/utils/test_path_utils.py"                      # US1
Task: "Write tests/tools/test_shell.py"                            # US3
Task: "Update docker-compose.yml and .env.example"                 # US4
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (config surface)
3. Complete Phase 3: User Story 1 — the actual security bug (sibling-prefix bypass) is fixed
4. **STOP and VALIDATE**: re-run the audit's own probe for real, confirm it now rejects

### Incremental Delivery

1. Setup + Foundational → config surface ready
2. Add User Story 1 → path containment bug fixed (MVP — closes the most severe gap)
3. Add User Story 2 → deliberate allowlist mechanism, verified as a no-op by default
4. Add User Story 3 → shell opt-in, timeout, honest description
5. Add User Story 4 → read-only source mount
6. Polish → ADR correction, repo-wide regression checks, real end-to-end container proof

---

## Notes

- [P] tasks touch different files with no dependency on an incomplete task
- Tests (T003, T006, T009) are written before their corresponding implementation
  (T004, T010–T011) per Constitution Principle IV, except T006/T007 which verify behavior
  T004 already delivers (per US2's dependency on US1)
- US2's and part of US4's "implementation" is deliberately light — the underlying mechanism
  is largely delivered by US1's fix and Foundational's config surface; this mirrors how the
  dual-Ollama-backend feature's US2/US3 were mostly verification of Foundational work
- Commit after each phase completes, split roughly as: Foundational+US1+US2 (path fix),
  US3 (shell gating), US4+ADR (mount + doc correction), then session-doc updates last
