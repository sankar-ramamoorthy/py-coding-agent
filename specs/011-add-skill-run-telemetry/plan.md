# Implementation Plan: Lightweight per-skill-run telemetry log

**Branch**: `add-skill-run-telemetry` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/011-add-skill-run-telemetry/spec.md`

## Summary

New module `py_mono/skill/telemetry.py`: `log_skill_run(skill, provider, model, duration_ms,
success, log_path=TELEMETRY_LOG)` appends one JSON line to `telemetry/skill_runs.jsonl`
(never raises — write failures are logged and swallowed); `read_skill_runs(log_path)` reads all
records back, skipping corrupt lines. Hooked into `py_mono/skill/approval.py`'s
`run_skill_safe` — the single existing chokepoint every skill execution already passes through
for approval/tool-access enforcement — timing the `skill.run(...)` call and logging exactly one
record per invocation, regardless of success or failure, via `try/finally`. Provider/model are
read from `context.session_manager.get_active_provider()` when available, falling back to
`<unknown>` (matching the `getattr(..., "model_name", "<unknown>")` pattern already used in
`py_mono/agent/agent.py`) when no session manager is present (e.g. some test harnesses).

## Technical Context

**Language/Version**: Python (unchanged)

**Primary Dependencies**: None new — stdlib `json`, `time`, `pathlib`, `datetime`

**Storage**: New flat-file log, `telemetry/skill_runs.jsonl`, one JSON object per line;
`telemetry/` added to `.gitignore` (pattern: `telemetry/*` + `!telemetry/.gitkeep`, matching the
existing `workspace/`/`dynamic_tools/` convention) since it's operational data, not source

**Testing**: `pytest`; new `tests/test_skill_telemetry.py` (5 tests) for the module itself, plus
3 new tests added to the existing `tests/test_skill_approval.py` covering the `run_skill_safe`
hook (success, failure, no-session-manager)

**Target Platform**: Unchanged

**Project Type**: Single project — one new module, one existing function instrumented

**Constraints**: Recording happens only at `run_skill_safe`'s single chokepoint; no per-skill
instrumentation added elsewhere

**Scale/Scope**: Small — one new ~60-line module, ~15 lines added to `run_skill_safe`, two test
files (one new, one extended)

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS — telemetry logic lives entirely in its own
  new module; `run_skill_safe` gains a `try/finally` around its existing `try/except`, not a
  restructure.
- **Principle III (Tool, Skill, and Playbook Separation)**: PASS — telemetry recording is
  runtime instrumentation of the execution layer, not new reasoning or orchestration logic.
- **Principle IV (Test Coverage for New Behavior)**: PASS — 8 new tests total (5 for the
  module, 3 for the `run_skill_safe` hook).
- **Principle V (Incremental Change Philosophy)**: PASS — `run_skill_safe`'s existing return
  value and exception behavior for callers are unchanged; telemetry is purely additive
  side-effect logging.

No violations.

## Project Structure

### Source Code (repository root)

```text
py_mono/skill/telemetry.py        # new: log_skill_run, read_skill_runs
py_mono/skill/approval.py         # run_skill_safe: telemetry hook added
tests/test_skill_telemetry.py     # new: 5 tests
tests/test_skill_approval.py      # extended: 3 new tests
.gitignore                        # telemetry/* + !telemetry/.gitkeep
telemetry/.gitkeep                # new: keeps the directory in version control
```

**Structure Decision**: No new top-level structure beyond the `telemetry/` runtime directory,
which follows the exact existing pattern already used for `workspace/` and `dynamic_tools/`.
