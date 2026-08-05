# Tasks: Model/task fitness check

**Input**: Design documents from `/specs/012-add-model-task-fitness-check/`

All tasks below were already executed and verified.

## Phase 1: Setup

- [x] T001 Confirm `py_mono/skill/telemetry.py`'s `read_skill_runs` (`ISS-013`, merged into
      this branch) is available as the data source

## Phase 2: User Story 1 - Get warned on a real failure history (Priority: P1)

- [x] T002 [US1] Create `py_mono/skill/fitness.py`: `check_model_fitness(skill, provider,
      model, log_path=TELEMETRY_LOG)` filters `read_skill_runs()` output to the exact matching
      triple, requires `MIN_SAMPLES = 3` before judging, considers only the most recent
      `RECENT_WINDOW = 5` matching records, and returns a warning string when the failure rate
      is `>= FAILURE_RATE_THRESHOLD (0.5)`, else `None`
- [x] T003 [US1] Instrument `run_skill_safe` in `py_mono/skill/approval.py`: call
      `check_model_fitness(skill_name, provider_name, model_name)` before timing execution;
      on success, prepend the warning (if any) to the returned result; on failure, no warning is
      attached
- [x] T004 [US1] [P] Add `tests/test_skill_fitness.py` (6 tests): no warning below minimum
      sample size, no warning below the failure-rate threshold, warning at/above the threshold
      (with correct counts in the message), other skill/provider/model combinations don't
      contaminate the result, only the recent window is considered (old failures outside the
      window don't count), missing telemetry file returns `None`
- [x] T005 [US1] [P] Add 3 tests to `tests/test_skill_approval.py`: a returned warning is
      prepended to a successful result, no prefix appears when no warning is returned, a failed
      run still raises with no warning attached
- [x] T006 [US1] Run `pytest tests/test_skill_fitness.py tests/test_skill_approval.py -v`:
      16 passed

## Phase 3: Polish & Cross-Cutting

- [x] T007 Run full suite + `compileall`: no new regressions (5 pre-existing, unrelated
      `ISS-005`-class failures present on a fresh `main` branch, tracked/fixed separately in
      PR #96); all 9 new tests included in the pass count

## Dependencies & Execution Order

Depends on `ISS-013` (`py_mono/skill/telemetry.py`, merged into this branch) already existing —
this feature has no data source without it, per Milestone 6's documented ordering.
