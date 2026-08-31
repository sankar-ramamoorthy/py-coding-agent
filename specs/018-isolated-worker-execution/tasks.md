# Tasks: Isolated Worker Execution

**Input**: Design documents from `specs/018-isolated-worker-execution/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by repository constitution for new behavior.

## Phase 1: Setup

- [ ] T001 Create Spec Kit artifacts in `specs/018-isolated-worker-execution/`

---

## Phase 2: Foundational

- [ ] T002 [P] Add skill worker subprocess/RPC implementation in `py_mono/skill/worker.py`
- [ ] T003 [P] Add worker contract tests in `tests/test_skill_worker.py`

---

## Phase 3: User Story 1 - Approved Skills Do Not Execute In Agent Process (Priority: P1)

- [ ] T004 [US1] Add skill proxy loading in `py_mono/skill/base.py`
- [ ] T005 [US1] Route skill proxies through workers in `py_mono/skill/approval.py`
- [ ] T006 [US1] Update skill load-gating tests in `tests/test_skill_load_gating.py`

---

## Phase 4: User Story 2 - Skills Use Narrow Tool RPC (Priority: P2)

- [ ] T007 [US2] Enforce allowed-tool RPC in `py_mono/skill/worker.py`
- [ ] T008 [US2] Add allowed/disallowed tool RPC tests in `tests/test_skill_worker.py`

---

## Phase 5: User Story 3 - Dynamic Tools Execute In A Worker (Priority: P3)

- [ ] T009 [US3] Add dynamic-tool worker execution in `py_mono/tools/worker.py`
- [ ] T010 [US3] Replace dynamic-tool imports with static metadata proxies in `py_mono/tools/tool_loader.py`
- [ ] T011 [US3] Update dynamic-tool tests in `tests/tools/test_tool_loader.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T012 [P] Update `README.md`, `docs/ISSUES.md`, `docs/PROJECT_STATUS.md`, `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md`, `docs/ROADMAP_PLAN.md`, and `docs/SESSION_LOG.md`
- [ ] T013 Run `uv run pytest -q`
- [ ] T014 Run `uv run python -m compileall -q py_mono skills`
- [ ] T015 Commit and merge `iss-008-isolated-worker-execution`

## Dependencies & Execution Order

- Phase 1 before all other work.
- Phase 2 before skill or dynamic-tool integration.
- User Story 1 before User Story 2.
- User Story 3 after the worker protocol is established.

## Implementation Strategy

Implement worker execution for skills first, then apply the same isolation principle to dynamic tools.
