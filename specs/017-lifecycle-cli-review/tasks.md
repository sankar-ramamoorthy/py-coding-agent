# Tasks: Lifecycle CLI Review Polish

**Input**: Design documents from `specs/017-lifecycle-cli-review/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by repository constitution for new behavior.

## Phase 1: Setup

- [ ] T001 Create Spec Kit artifacts in `specs/017-lifecycle-cli-review/`

---

## Phase 2: Foundational

- [ ] T002 [P] Add report loading and CLI summary helpers in `py_mono/skill/reporting.py`
- [ ] T003 [P] Add candidate/report path accessors in `py_mono/skill/base.py` if needed

---

## Phase 3: User Story 1 - Review Pending Candidate From CLI (Priority: P1)

**Goal**: One command reviews a pending candidate or proposed skill report.

**Independent Test**: Run `/skill review <name>` against fixture reports and inspect output.

- [ ] T004 [US1] Recognize `/skill review <name>` in `py_mono/agent/agent.py`
- [ ] T005 [US1] Render lifecycle report summaries in `py_mono/agent/agent.py`
- [ ] T006 [US1] Add review command tests in `tests/test_special_commands.py`

---

## Phase 4: User Story 2 - Discover Review State In Existing Commands (Priority: P2)

**Goal**: List/help commands reveal pending lifecycle review state.

**Independent Test**: Run list/help against fixture skills with candidates.

- [ ] T007 [US2] Mark pending candidates in `/skill list` output in `py_mono/agent/agent.py`
- [ ] T008 [US2] Add pending candidate notice to `/skill help <name>` in `py_mono/agent/agent.py`
- [ ] T009 [US2] Add list/help tests in `tests/test_special_commands.py`

---

## Phase 5: User Story 3 - Approve With Clear Outcome (Priority: P3)

**Goal**: Approval messages explain candidate promotion or rejection.

**Independent Test**: Approve valid and invalid candidates and inspect output.

- [ ] T010 [US3] Improve candidate approval success/failure messages in `py_mono/agent/agent.py`
- [ ] T011 [US3] Add approval-message tests in `tests/test_generate_skill.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T012 [P] Update `README.md`, `docs/ISSUES.md`, `docs/PROJECT_STATUS.md`, `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md`, `docs/ROADMAP_PLAN.md`, and `docs/SESSION_LOG.md`
- [ ] T013 Run `uv run pytest -q`
- [ ] T014 Run `uv run python -m compileall -q py_mono skills`
- [ ] T015 Commit and merge `iss-019-lifecycle-cli-polish`

## Dependencies & Execution Order

- Phase 1 before all other work.
- Phase 2 before review/list/help/approve command changes.
- User Story 1 before User Story 2 because list/help point to review.
- User Story 3 can follow once candidate path/report behavior is available.

## Parallel Opportunities

- T002 and T003 can be done in parallel if registry accessors are needed.
- Tests for review/list/help can be prepared alongside command implementation.

## Implementation Strategy

Deliver `/skill review <name>` first, then make list/help point to it, then clarify approval outcomes.
