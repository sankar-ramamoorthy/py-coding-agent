# Tasks: Lightweight per-skill-run telemetry log

**Input**: Design documents from `/specs/011-add-skill-run-telemetry/`

All tasks below were already executed and verified.

## Phase 1: Setup

- [x] T001 Identify the single chokepoint all skill execution passes through:
      `run_skill_safe` in `py_mono/skill/approval.py`, already responsible for
      approval/tool-access enforcement (ISS-003)

## Phase 2: User Story 1 - Every skill run leaves a usable telemetry record (Priority: P1)

- [x] T002 [US1] Create `py_mono/skill/telemetry.py`: `log_skill_run(skill, provider, model,
      duration_ms, success, log_path=TELEMETRY_LOG)` appends one JSON line to
      `telemetry/skill_runs.jsonl`, catching `OSError` and logging a warning rather than raising
- [x] T003 [US1] [P] Add `read_skill_runs(log_path)` to the same module: reads all records back,
      skipping corrupt lines with a warning, returning `[]` if the file doesn't exist
- [x] T004 [US1] Instrument `run_skill_safe` in `py_mono/skill/approval.py`: resolve
      provider/model from `context.session_manager.get_active_provider()` (falling back to
      `<unknown>`/`<unknown>` if no session manager or lookup fails), time `skill.run(...)` with
      `time.monotonic()`, and log exactly one record via `try/finally` regardless of success or
      failure
- [x] T005 [US1] [P] Add `tests/test_skill_telemetry.py` (5 tests): one JSON line per call,
      appends without truncating across multiple calls, creates parent directories, missing-file
      read returns `[]`, corrupt lines are skipped on read
- [x] T006 [US1] [P] Add 3 tests to `tests/test_skill_approval.py`: successful run logs one
      record with `success: true`, a failing skill still logs one record with `success: false`
      before the `RuntimeError` propagates, a context with `session_manager=None` logs
      `<unknown>`/`<unknown>` without crashing
- [x] T007 [US1] Add `telemetry/` to `.gitignore` (`telemetry/*` + `!telemetry/.gitkeep`,
      matching the existing `workspace/`/`dynamic_tools/` pattern) and create
      `telemetry/.gitkeep`
- [x] T008 [US1] Run `pytest tests/test_skill_telemetry.py tests/test_skill_approval.py -v`:
      12 passed

## Phase 3: Polish & Cross-Cutting

- [x] T009 Run full suite + `compileall`: no new regressions (5 pre-existing, unrelated
      `ISS-005`-class failures present on a fresh `main` branch, tracked/fixed separately in
      PR #96); all 8 new tests included in the pass count

## Dependencies & Execution Order

Single linear sequence — the module (T002-T003) must exist before it can be imported into
`run_skill_safe` (T004), which must exist before its behavior can be tested (T006).
