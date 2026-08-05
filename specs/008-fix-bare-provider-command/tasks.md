# Tasks: Fix bare `/provider` falling through to the LLM

**Input**: Design documents from `/specs/008-fix-bare-provider-command/`

All tasks below were already executed and verified.

## Phase 1: Setup

- [x] T001 Reproduce the bug: confirm `agent._is_special_command("/provider")` returns `False`
      before the fix, tracing through `_is_special_command`'s tuple check and
      `text.startswith("/provider ")` check in `py_mono/agent/agent.py`

## Phase 2: User Story 1 - Typing `/provider` alone shows usage (Priority: P1)

- [x] T002 [US1] Add `"/provider"` to the exact-match tuple in `_is_special_command`
      (`py_mono/agent/agent.py`)
- [x] T003 [US1] Add `if text == "/provider": return "Usage: /provider <provider> [model]"` in
      `_handle_special_command`, before the existing `text.startswith("/provider ")` branch
- [x] T004 [US1] Add `tests/test_special_commands.py` with a `make_agent()` helper (real `Agent`
      + `SessionManager`, mirroring `tests/test_skill_load_gating.py`'s pattern) and 5 tests:
      bare `/provider` recognized as special + returns usage, trailing-space-only still returns
      usage (regression guard), `/providers` (plural) unaffected, `/provider <valid-name>` still
      switches successfully
- [x] T005 [US1] Run `pytest tests/test_special_commands.py -v`: 5 passed
- [x] T006 [US1] Run full suite + `compileall`: no new regressions (5 pre-existing, unrelated
      `ISS-005` failures present, tracked/fixed separately in PR #96)

## Dependencies & Execution Order

Single linear sequence.
