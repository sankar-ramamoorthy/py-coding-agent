# Implementation Plan: Fix bare `/provider` falling through to the LLM

**Branch**: `fix-bare-provider-command` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/008-fix-bare-provider-command/spec.md`

## Summary

`Agent._is_special_command` matched `/provider ` (trailing space required) or the exact string
`/providers`, so bare `/provider` (no space) matched neither and fell through to the LLM. Added
the exact string `"/provider"` to the recognized-commands tuple in `_is_special_command`, and a
matching `if text == "/provider":` branch in `_handle_special_command` returning the same usage
message already used for the trailing-space case.

## Technical Context

**Language/Version**: Python (unchanged)

**Primary Dependencies**: None new

**Storage**: N/A

**Testing**: `pytest`, new `tests/test_special_commands.py` constructing a real `Agent` +
`SessionManager` (mirrors the existing pattern in `tests/test_skill_load_gating.py`'s
`make_agent` helper) rather than mocking the dispatch methods

**Target Platform**: Unchanged

**Project Type**: Single project — one existing file changed

**Constraints**: Fix confined to `py_mono/agent/agent.py`'s special-command dispatch; no other
command's matching logic touched

**Scale/Scope**: Minimal — two small additions to two existing methods, one new test file

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS — two one-line additions to existing
  methods, no restructuring of command dispatch.
- **Principle IV (Test Coverage for New Behavior)**: PASS — `tests/test_special_commands.py`
  added (5 tests: bare `/provider` recognized + shows usage, trailing-space-only unaffected,
  `/providers` unaffected, valid-argument switching unaffected).
- **Principle V (Incremental Change Philosophy)**: PASS — no existing command's behavior
  changed, only a previously-unhandled input shape now handled.

No violations.

## Project Structure

### Source Code (repository root)

```text
py_mono/agent/agent.py           # _is_special_command + _handle_special_command: bare "/provider"
tests/test_special_commands.py   # new: 5 tests
```

**Structure Decision**: No new structure — one existing file changed, one new flat test file
(matches `tests/test_skill_load_gating.py`'s existing flat placement convention).
