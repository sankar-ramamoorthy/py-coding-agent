# Tasks: Lifecycle State Reports

**Input**: Design documents from `specs/016-lifecycle-state-reports/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Required by repository constitution for new behavior.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Phase 1: Setup

**Purpose**: Prepare feature artifacts and reporting module location.

- [ ] T001 Create Spec Kit artifacts in `specs/016-lifecycle-state-reports/`

---

## Phase 2: Foundational

**Purpose**: Core report serialization shared by all user stories.

- [ ] T002 [P] Add lifecycle report data models and Markdown/JSON rendering in `py_mono/skill/reporting.py`
- [ ] T003 [P] Add report serialization tests in `tests/test_skill_lifecycle_reporting.py`

---

## Phase 3: User Story 1 - Inspect Latest Candidate Report (Priority: P1)

**Goal**: Successful candidate proposals leave durable report files.

**Independent Test**: Generate a candidate with stubbed LLM output and inspect report files under the skill or candidate directory.

- [ ] T004 [US1] Wire successful generation/regeneration report writing into `skills/generate_skill/skill.py`
- [ ] T005 [US1] Add generator integration tests for successful report files in `tests/test_generate_skill.py`

---

## Phase 4: User Story 2 - Preserve Failure Evidence (Priority: P2)

**Goal**: Failed validation and smoke-test attempts leave durable reports.

**Independent Test**: Force validation and smoke-test failures and verify report contents.

- [ ] T006 [US2] Wire failed lifecycle report writing into `skills/generate_skill/skill.py`
- [ ] T007 [US2] Add generator integration tests for failed lifecycle reports in `tests/test_generate_skill.py`

---

## Phase 5: User Story 3 - Carry Evolution Context Into Reports (Priority: P3)

**Goal**: Evolution proposals include triggering failure context in durable reports.

**Independent Test**: Stub failure context, run evolution, and inspect report JSON/Markdown.

- [ ] T008 [US3] Persist evolution failure context in lifecycle reports from `skills/generate_skill/skill.py`
- [ ] T009 [US3] Add evolution report assertions in `tests/test_generate_skill.py`

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation and validation before merge.

- [ ] T010 [P] Update `README.md`, `docs/ROADMAP_PLAN.md`, `docs/PROJECT_STATUS.md`, `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md`, `docs/ISSUES.md`, and `docs/SESSION_LOG.md`
- [ ] T011 Run `uv run pytest -q`
- [ ] T012 Run `uv run python -m compileall -q py_mono skills`
- [ ] T013 Commit and merge `iss-018-lifecycle-reports`

## Dependencies & Execution Order

- Phase 1 before all other work.
- Phase 2 before all user stories.
- User Story 1 before User Story 2 and User Story 3 because it establishes the success-path integration.
- Polish after all stories.

## Parallel Opportunities

- T002 and T003 can be developed together.
- Documentation updates can be prepared while final validation runs.

## Implementation Strategy

Deliver the MVP by writing reports for successful candidate proposals first, then add failure reports and evolution context. Keep the report writer independent from approval and registry loading.
