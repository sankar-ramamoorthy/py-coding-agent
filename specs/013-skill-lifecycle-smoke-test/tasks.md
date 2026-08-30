# Tasks: Skill Lifecycle Smoke Test

**Input**: Design documents from `/specs/013-skill-lifecycle-smoke-test/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included because this feature changes skill lifecycle behavior and the
repository constitution requires coverage for new behavior.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Phase 1: Setup

**Purpose**: Confirm the implementation surface and add focused test scaffolding.

- [x] T001 Confirm current `skills/generate_skill/skill.py` generation flow and existing
      `py_mono/skill/validator.py` validation contracts before editing
- [x] T002 [P] Create `tests/test_skill_lifecycle.py` with helper fixtures for lifecycle stage
      result and smoke-test behavior
- [x] T003 [P] Create `tests/test_generate_skill.py` with stubs for LLM responses, session
      manager, and temporary skills directory behavior

---

## Phase 2: Foundational

**Purpose**: Add reusable lifecycle primitives needed by all user stories.

- [x] T004 Create `py_mono/skill/lifecycle.py` with `LifecycleStageResult`,
      `SkillLifecycleRun`, and stable stage/status constants
- [x] T005 Add lifecycle formatting helpers in `py_mono/skill/lifecycle.py` that render ordered
      stage results for user-facing output
- [x] T006 Add a smoke-test helper in `py_mono/skill/lifecycle.py` that can instantiate validated
      generated skill code and run it once with a synthetic request without touching the approval
      ledger
- [x] T007 Run `uv run pytest tests/test_skill_lifecycle.py -v` for
      `tests/test_skill_lifecycle.py` and confirm the new helper tests fail before implementation
      is complete, then pass after T004-T006

---

## Phase 3: User Story 1 - See Lifecycle Results Before Approval (Priority: P1) MVP

**Goal**: Successful skill generation reports Critique, Generate, Validate, Test, and Propose
before the user approves anything.

**Independent Test**: Generate a simple skill through `GenerateSkill.run()` with stubbed LLM
responses and confirm all lifecycle stages are reported while final status remains proposed.

### Tests for User Story 1

- [x] T008 [P] [US1] Add a success-path test in `tests/test_generate_skill.py` asserting the
      response includes ordered lifecycle stages and `Status: proposed`
- [x] T009 [P] [US1] Add a test in `tests/test_generate_skill.py` asserting successful lifecycle
      completion does not mark the generated skill as approved

### Implementation for User Story 1

- [x] T010 [US1] Update `skills/generate_skill/skill.py` to create and maintain lifecycle stage
      results through critique, generation, validation, test, and propose
- [x] T011 [US1] Update `skills/generate_skill/skill.py` response building to include the
      lifecycle report while preserving existing review/approve/run next steps
- [x] T012 [US1] Run `uv run pytest tests/test_generate_skill.py tests/test_skill_lifecycle.py -v`
      and confirm US1 tests pass

---

## Phase 4: User Story 2 - Catch Smoke-Test Failures Before Proposal (Priority: P2)

**Goal**: Generated code that passes static validation but fails at runtime is reported as a Test
stage failure and is not presented as approval-ready.

**Independent Test**: Stub generated code whose `run()` raises, then confirm Test fails and
Propose does not pass.

### Tests for User Story 2

- [x] T013 [P] [US2] Add a smoke-test failure test in `tests/test_skill_lifecycle.py`
- [x] T014 [P] [US2] Add a generate-skill integration test in `tests/test_generate_skill.py`
      asserting Test failure blocks approval-ready presentation

### Implementation for User Story 2

- [x] T015 [US2] Update `py_mono/skill/lifecycle.py` smoke-test helper to return actionable
      failure reasons for exceptions and unusable output
- [x] T016 [US2] Update `skills/generate_skill/skill.py` to stop at Test failure, report skipped
      proposal, and avoid returning approval-ready next steps for the failed output
- [x] T017 [US2] Run `uv run pytest tests/test_generate_skill.py tests/test_skill_lifecycle.py -v`
      and confirm US2 tests pass

---

## Phase 5: User Story 3 - Preserve the Existing Approval Boundary (Priority: P3)

**Goal**: Passing the lifecycle still leaves the existing explicit approval action as the only
path to normal execution.

**Independent Test**: Complete a successful generation flow and confirm the generated skill is
not registry-loaded or ledger-approved until the existing approval command runs.

### Tests for User Story 3

- [x] T018 [P] [US3] Add a regression test in `tests/test_generate_skill.py` asserting no approval
      ledger entry is written by lifecycle success
- [x] T019 [P] [US3] Add a regression test in `tests/test_generate_skill.py` asserting generated
      `SKILL.md` status remains proposed

### Implementation for User Story 3

- [x] T020 [US3] Audit `skills/generate_skill/skill.py` and `py_mono/skill/lifecycle.py` to ensure
      no code path calls approval-ledger write helpers during lifecycle success
- [x] T021 [US3] Run `uv run pytest tests/test_skill_approval.py tests/test_generate_skill.py -v`
      and confirm existing approval behavior is unchanged

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Final verification and documentation alignment.

- [x] T022 [P] Update `docs/ISSUES.md` `ISS-015` detail with implementation summary after code is
      complete
- [x] T023 [P] Update `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md`, and
      `docs/SESSION_LOG.md` with implementation results
- [x] T024 Run `uv run pytest -q` for the repository test suite under `tests/`
- [x] T025 Run `uv run python -m compileall -q py_mono skills` for `py_mono/` and `skills/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on setup test scaffolding.
- **US1 (Phase 3)**: Depends on lifecycle primitives.
- **US2 (Phase 4)**: Depends on smoke-test primitives and US1 response integration.
- **US3 (Phase 5)**: Depends on US1 success path and US2 failure path.
- **Polish (Phase 6)**: Depends on all selected stories being complete.

### User Story Dependencies

- **User Story 1 (P1)**: MVP; complete first.
- **User Story 2 (P2)**: Builds on the smoke-test stage surfaced by US1.
- **User Story 3 (P3)**: Verifies the approval boundary after lifecycle behavior exists.

### Parallel Opportunities

- T002 and T003 can be created in parallel.
- T008 and T009 can be written in parallel after foundational helpers exist.
- T013 and T014 can be written in parallel.
- T018 and T019 can be written in parallel.
- Documentation updates T022 and T023 can be prepared in parallel after implementation results
  are known.

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 only.
3. Validate that a successful generated skill shows all five lifecycle stages and remains
   proposed.

### Incremental Delivery

1. Add lifecycle primitives and success reporting.
2. Add smoke-test failure handling.
3. Verify the approval boundary remains unchanged.
4. Run focused tests, full test suite, and compileall before handoff.
