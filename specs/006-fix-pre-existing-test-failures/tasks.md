# Tasks: Fix pre-existing test failures

**Input**: Design documents from `/specs/006-fix-pre-existing-test-failures/`

**Note**: All tasks below were already executed and verified before this file was generated
(this spec documents completed root-cause work, per this repo's SDD process for bug-fix issues
— see `specs/005-fix-ollama-thinking-response/` for precedent). Every task is checked off.

## Phase 1: Setup

- [x] T001 Reproduce the full failure set on a clean `main` checkout via `python -m pytest -q`
      to confirm scope before making any change (6 collection errors initially traced to a
      missing `requests` dependency in the ad-hoc shell environment, resolved by running via
      the project's `.venv`; true failure set: 5 failed tests across 3 files)

## Phase 2: Foundational

No shared blocking prerequisites — the three findings (US1's three sub-bugs, US2) are
independent fixes in independent files. Skipping to per-story phases.

## Phase 3: User Story 1 - The test suite reflects real problems, not stale drift (Priority: P1)

**Goal**: Every test failure means something real is broken, not test/implementation drift.

**Independent Test**: `python -m pytest -q` on a clean checkout produces zero unexplained failures.

- [x] T002 [US1] Root-cause `tests/test_listallpy_skill.py` failures: confirm
      `skills/listallpy/skill.py`'s `run()` calls `Path(context.workspace_root).rglob("*.py")`
      directly instead of `context.agent_tools["list_files"]`, violating ADR-016 and bypassing
      the tests' `list_files` mock
- [x] T003 [US1] Fix `skills/listallpy/skill.py`: rewrite `run()` to call
      `context.agent_tools["list_files"].run(path=".")`, parse the returned JSON, and filter
      `type == "file"` and `name.endswith(".py")`
- [x] T004 [US1] Root-cause `tests/tools/test_create_tool.py` failures: confirm
      `py_mono/tools/create_tool.py` returns `"Invalid tool name."` (test expects
      `"Error: tool name must be a valid Python identifier."`) and a success message with no
      file path (test expects the resolved path present), and confirm via the file's other
      3 already-passing tests that the wrapped-`Tool`-schema contract is the intentional,
      relied-upon behavior (not something to remove)
- [x] T005 [US1] Fix `py_mono/tools/create_tool.py`: update invalid-name message to
      `"Error: tool name must be a valid Python identifier."` and success message to
      `f"✅ Tool '{name}' created with schema: {path}"`
- [x] T006 [US1] Update `tests/tools/test_create_tool.py::test_create_tool_writes_file_for_valid_name`
      to use a code snippet containing an actual function and assert against the wrapped-output
      contract (file contains the given code, result contains the resolved path) instead of a
      verbatim-write assumption
- [x] T007 [US1] [P] Update `tests/tools/test_create_tool.py::test_create_tool_rejects_invalid_module_name`
      to assert the corrected message text
- [x] T008 [US1] Run `python -m pytest -q` and `python -m compileall -q py_mono skills` to
      confirm all of User Story 1's failures are resolved with no new regressions

**Checkpoint**: `listallpy` and `create_tool` failures resolved independently of User Story 2.

## Phase 4: User Story 2 - Skill approval survives being checked out on a different platform (Priority: P1)

**Goal**: A skill's recorded approval must not silently invalidate itself from a checkout-platform
line-ending difference alone.

**Independent Test**: Approve a skill, simulate a different-line-ending re-checkout with no
content change, confirm it's still recognized as approved; confirm a genuine content change is
still correctly rejected.

- [x] T009 [US2] Root-cause `tests/test_skill_load_gating.py::test_all_real_approved_skills_still_load`
      failure: compare `skills/.approvals.json`'s recorded hash for `listallpy` against
      `git show HEAD:skills/listallpy/skill.py` (matches — 760 bytes, LF) vs. the on-disk
      working-tree file (783 bytes, CRLF, `core.autocrlf=true`) — confirms the approval was
      recorded against LF content later rewritten to CRLF by a platform checkout, with no actual
      content change
- [x] T010 [US2] Verify this is systemic, not a one-off: script-check all 9 ledger entries'
      hashes against their git blob (LF) content — 7 of 9 mismatch, confirming this would break
      almost every approved skill's status on a Linux CI runner (directly relevant to `ISS-012`,
      same milestone)
- [x] T011 [US2] Fix `py_mono/skill/approval_ledger.py`: normalize `\r\n` → `\n` in
      `hash_file()` before hashing, with a comment explaining the `core.autocrlf` root cause
- [x] T012 [US2] Regenerate `skills/.approvals.json`: recompute all 9 entries' `sha256` using the
      fixed `hash_file()`, preserving existing `recorded_at`/`seeded` metadata unchanged
- [x] T013 [US2] [P] Add `tests/test_approval_ledger.py`: `test_hash_file_ignores_crlf_vs_lf`
      (CRLF/LF byte-equivalent content hashes identically), `test_is_approved_survives_line_ending_conversion`
      (approval survives a simulated CRLF re-checkout with no content change),
      `test_is_approved_still_rejects_real_content_changes` (a genuine content change still
      correctly invalidates approval — the fix must not weaken the ISS-003 approval gate)
- [x] T014 [US2] Run `python -m pytest -q tests/test_approval_ledger.py tests/test_skill_load_gating.py`
      to confirm the fix and that no other approved skill regressed

**Checkpoint**: All currently-approved skills load successfully regardless of checkout platform.

## Phase 5: Polish & Cross-Cutting

- [x] T015 Run the full suite once more (`python -m pytest -q`): 104 passed, 1 skipped
      (pre-existing, environment-specific Windows symlink-privilege skip, unrelated to this
      fix) — down from 6 collection errors / 5 failures
- [x] T016 Run `python -m compileall -q py_mono skills`: clean
- [x] T017 Update `docs/ISSUES.md` ISS-005 status and `docs/ROADMAP_PLAN.md` Milestone 6 tracking
      once this branch merges (tracked as a follow-up commit, not part of this spec's code diff)

## Dependencies & Execution Order

- User Story 1 (T002–T008) and User Story 2 (T009–T014) are independent — different files, no
  shared state — and were fixed in parallel in practice, not sequentially gated on each other.
- Phase 5 (Polish) depends on both stories being complete (full-suite verification needs every
  fix present).

## Parallel Execution Notes

- Within User Story 1, T007 was independent of T006 (different assertions in the same file,
  no shared fixture state) — marked `[P]`.
- Within User Story 2, T013 (new test file) was independent of T011/T012 being finished first
  in sequence (test written against the target behavior, then run once both were in place) —
  marked `[P]` for authoring, though verification (T014) naturally comes after.
- User Story 1 and User Story 2 have no file overlap and were executed independently.

## Implementation Strategy

Both user stories are P1 and were completed together in one pass — there is no meaningful MVP
subset smaller than "all pre-existing failures fixed," since `ISS-012` (Milestone 6 CI) depends
on the full suite being green, not a partial fix.
