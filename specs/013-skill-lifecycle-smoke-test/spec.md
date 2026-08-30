# Feature Specification: Skill Lifecycle Smoke Test

**Feature Branch**: `[013-skill-lifecycle-smoke-test]`

**Created**: 2026-08-30

**Status**: Implemented

**Input**: User description: "Start Milestone 7 with the narrowest valuable slice: Critique -> Generate -> Validate -> Test(smoke run) -> Propose."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See Lifecycle Results Before Approval (Priority: P1)

A user creating a new skill can see that the draft was critiqued, generated, validated, and
smoke-tested before it is presented for approval.

**Why this priority**: This is the core M7 value. It reduces blind approval of generated skill
code by showing whether the skill passed the minimum lifecycle checks before a human reviews it.

**Independent Test**: Can be fully tested by creating a simple new skill request and confirming
that the result reports each lifecycle stage and leaves the skill in proposed state.

**Acceptance Scenarios**:

1. **Given** a valid skill request, **When** the user generates the skill, **Then** the user sees
   a completed critique, generation, validation, and smoke-test result before approval.
2. **Given** a generated skill that passes all pre-approval checks, **When** the lifecycle
   completes, **Then** the skill is proposed for review and is not silently approved or runnable
   without the existing approval action.

---

### User Story 2 - Catch Smoke-Test Failures Before Proposal (Priority: P2)

A user receives a clear failure result when generated skill code passes static validation but
does not run successfully against a trivial synthetic input.

**Why this priority**: Static validation confirms a skill is acceptable to inspect, not that it
works. A smoke-test stage catches the next class of failure before approval.

**Independent Test**: Can be fully tested by generating or substituting a skill implementation
that passes static checks but raises during a trivial run, then confirming the lifecycle reports
the failed stage and does not present the skill as ready for approval.

**Acceptance Scenarios**:

1. **Given** a generated skill that passes static validation but fails its smoke run, **When**
   the lifecycle reaches the test stage, **Then** the user sees the failure reason and the skill
   is not presented as approval-ready.
2. **Given** a smoke-test failure, **When** the lifecycle stops, **Then** the user can retry
   generation without the failed output being treated as approved.

---

### User Story 3 - Preserve the Existing Approval Boundary (Priority: P3)

A user can rely on the current proposed-to-approved review boundary staying intact while the new
pre-approval lifecycle adds more evidence.

**Why this priority**: M7 should improve review quality without weakening the security and
governance work already completed in M5 and M6.

**Independent Test**: Can be fully tested by completing the lifecycle for a valid skill and
confirming the existing approval step is still required before normal execution.

**Acceptance Scenarios**:

1. **Given** a skill that passes critique, validation, and smoke testing, **When** generation
   completes, **Then** the skill remains proposed until the user explicitly approves it.
2. **Given** a proposed skill whose implementation changes after lifecycle completion, **When**
   the user attempts to run it without approval, **Then** the existing approval gate still blocks
   execution.

### Edge Cases

- The draft skill spec duplicates an existing skill or requests behavior outside the allowed
  tool/skill boundary.
- Generation succeeds but static validation rejects the generated implementation.
- Static validation succeeds but the smoke run raises an exception or returns unusable output.
- The lifecycle retries a failed generation path and reaches the configured retry limit.
- Telemetry logging fails or is unavailable during the lifecycle.
- The user regenerates an existing approved skill; this first slice does not need to show a
  last-approved diff, but it must not weaken the existing approval state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST present skill creation as an ordered lifecycle with these stages:
  Critique, Generate, Validate, Test, and Propose.
- **FR-002**: The system MUST critique the draft skill request or specification before presenting
  generated implementation results.
- **FR-003**: The critique result MUST identify blocking policy or lifecycle issues that should
  stop generation or proposal.
- **FR-004**: The system MUST validate generated skill implementation output before any smoke run
  is attempted.
- **FR-005**: The system MUST run one smoke test for generated skill implementation that passes
  validation.
- **FR-006**: The smoke test MUST use a trivial synthetic input suitable for confirming that the
  generated skill can execute at least once.
- **FR-007**: The system MUST show users which lifecycle stage failed and provide the actionable
  failure reason.
- **FR-008**: The system MUST keep generated skills in proposed state until the existing approval
  action is explicitly completed.
- **FR-009**: The system MUST NOT approve, load, or run generated skill code automatically as a
  result of passing the new lifecycle checks.
- **FR-010**: The lifecycle MUST respect the existing retry limit behavior and clearly report
  when retries are exhausted.
- **FR-011**: The lifecycle MUST reuse the existing skill telemetry stream where skill execution
  events are recorded, without requiring a second independent run log for this slice.
- **FR-012**: The feature MUST leave diff-on-regeneration, production-failure self-repair, signed
  packages, and full worker isolation out of this first slice.

### Key Entities

- **Skill Lifecycle Run**: One attempt to take a skill request through critique, generation,
  validation, smoke testing, and proposal.
- **Lifecycle Stage Result**: The outcome of one stage, including status, user-facing message,
  and failure reason when applicable.
- **Proposed Skill**: A generated skill artifact awaiting explicit user approval.
- **Smoke Test Result**: The outcome of the one synthetic execution check for a generated skill.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can determine the status of all five lifecycle stages for a generated skill
  in one result without inspecting source files manually.
- **SC-002**: 100% of generated skills that fail validation or smoke testing are withheld from
  approval-ready presentation.
- **SC-003**: 100% of generated skills that pass the lifecycle still require the existing explicit
  approval action before normal execution.
- **SC-004**: A basic skill generation flow that passes all stages completes with no more than one
  additional user action compared with the current generation flow.
- **SC-005**: Smoke-test failures identify the failed stage and a failure reason clear enough for a
  user or future agent session to decide whether to retry generation.

## Assumptions

- The target user is the same single operator who currently creates, reviews, approves, and runs
  skills in this repository.
- The first slice is limited to new or regenerated skill creation before approval; production
  failure-driven evolution is deferred.
- The existing approval gate remains the source of truth for whether a skill can be loaded and
  run normally.
- A single synthetic smoke run is enough for this milestone slice; comprehensive test generation
  is future work.
- The existing telemetry foundation from M6 is available and should be extended only as needed.
