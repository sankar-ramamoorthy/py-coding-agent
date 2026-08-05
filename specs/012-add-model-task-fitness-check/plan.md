# Implementation Plan: Model/task fitness check

**Branch**: `add-model-task-fitness-check` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/012-add-model-task-fitness-check/spec.md`

## Summary

New module `py_mono/skill/fitness.py`: `check_model_fitness(skill, provider, model,
log_path=TELEMETRY_LOG)` reads telemetry via `read_skill_runs` (`ISS-013`), filters to records
matching the exact (skill, provider, model) triple, and — only once at least `MIN_SAMPLES` (3)
matching records exist — checks whether the failure rate over the most recent `RECENT_WINDOW`
(5) matching records is at or above `FAILURE_RATE_THRESHOLD` (0.5). Returns a warning string if
so, else `None`. Hooked into `run_skill_safe` (`py_mono/skill/approval.py`) right before timing
the skill's execution: on a successful run, if a warning was returned, it's prepended to the
result string; on a failed run, no warning is attached (there's no successful result to prepend
to, and the run's own `RuntimeError` is already the signal).

## Technical Context

**Language/Version**: Python (unchanged)

**Primary Dependencies**: None new — reuses `py_mono.skill.telemetry.read_skill_runs`
(`ISS-013`) directly

**Storage**: Reads the existing `telemetry/skill_runs.jsonl` (`ISS-013`); writes nothing new

**Testing**: `pytest`; new `tests/test_skill_fitness.py` (6 tests) for the check itself, plus 3
new tests added to `tests/test_skill_approval.py` covering the `run_skill_safe` integration
(warning prepended on success, no warning when none returned, no warning on a failed run)

**Target Platform**: Unchanged

**Project Type**: Single project — one new module, one existing function extended

**Constraints**: Fitness logic lives entirely in its own module; `run_skill_safe` gains one
warning-check call and one conditional string prefix, no other behavior changed

**Scale/Scope**: Small — one new ~50-line module, ~5 lines added to `run_skill_safe`, two test
files (one new, one extended)

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS — fitness logic is fully isolated in its own
  module; `run_skill_safe`'s change is a single warning-check call plus a conditional prefix on
  the already-existing return statement.
- **Principle IV (Test Coverage for New Behavior)**: PASS — 9 new tests total (6 for the module
  covering sample-size/threshold/window/cross-contamination edge cases, 3 for the
  `run_skill_safe` integration).
- **Principle V (Incremental Change Philosophy)**: PASS — a skill's result is unchanged unless a
  warning genuinely applies; no existing interface or return type changed (still a plain string).

No violations.

## Project Structure

### Source Code (repository root)

```text
py_mono/skill/fitness.py           # new: check_model_fitness
py_mono/skill/approval.py          # run_skill_safe: fitness-check hook added
tests/test_skill_fitness.py        # new: 6 tests
tests/test_skill_approval.py       # extended: 3 new tests
```

**Structure Decision**: No new structure — one new module alongside the existing
`py_mono/skill/telemetry.py` and `py_mono/skill/approval.py`, one existing function extended.
