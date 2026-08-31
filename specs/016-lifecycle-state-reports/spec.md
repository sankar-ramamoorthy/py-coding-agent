# Feature Specification: Lifecycle State Reports

**Feature Branch**: `iss-018-lifecycle-reports`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "ISS-018: persist and report skill lifecycle state. Add durable, inspectable lifecycle state for generated and regenerated skill candidates, including candidate/lifecycle metadata, lifecycle reports, baseline references, rendered diff records, smoke-test results, and failure-context records. Keep this file-backed and lightweight; no dashboard."

## User Scenarios & Testing

### User Story 1 - Inspect Latest Candidate Report (Priority: P1)

A human reviewer can inspect a durable report for the latest generated, regenerated, or evolved skill candidate after the generator finishes.

**Why this priority**: The lifecycle report is the main artifact that turns a transient terminal response into durable review evidence.

**Independent Test**: Generate or regenerate a skill candidate and verify a report file remains available with lifecycle stages, candidate location, smoke-test outcome, and approval guidance.

**Acceptance Scenarios**:

1. **Given** a new skill generation succeeds, **When** the user inspects the generated skill directory, **Then** a lifecycle report exists and names the proposed files, lifecycle stage results, smoke-test result, and next approval command.
2. **Given** a skill regeneration succeeds, **When** the user inspects the candidate directory, **Then** the lifecycle report identifies the approved baseline status and includes separate rendered diffs for `SKILL.md` and `skill.py`.

---

### User Story 2 - Preserve Failure Evidence (Priority: P2)

A maintainer can inspect why a candidate was not proposed after generation, validation, smoke test, or save failure.

**Why this priority**: Failed lifecycle attempts are the hardest to reconstruct from terminal output and are useful for debugging models, prompts, and skill design.

**Independent Test**: Force a lifecycle failure and verify a report remains available with the failure stage, skipped stages, and next suggested action.

**Acceptance Scenarios**:

1. **Given** generated code fails validation, **When** the generation command returns, **Then** a durable report records the failed validation details and marks later stages as skipped.
2. **Given** a smoke test fails, **When** the generation command returns, **Then** a durable report records the smoke-test request and failure reason.

---

### User Story 3 - Carry Evolution Context Into Reports (Priority: P3)

A reviewer can see the failure context that caused an evolved skill proposal.

**Why this priority**: Evolution proposals are only understandable if the triggering failure remains attached to the candidate review record.

**Independent Test**: Evolve a skill from telemetry failure context and verify the report includes the original request, failure, provider, model, and timestamp.

**Acceptance Scenarios**:

1. **Given** a skill has actionable failure telemetry, **When** the user runs evolution, **Then** the report includes the failure context used to generate the candidate.

### Edge Cases

- If a lifecycle run fails before any files can be written, the system still writes a report under the skill directory when possible.
- If a baseline is unavailable for regeneration, the report records that reason instead of implying a diff exists.
- If report writing fails because of filesystem permissions, generation output still returns and the failure is surfaced without approving or loading the skill.
- Existing approved skills and approval ledger semantics remain unchanged.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST write a durable lifecycle report for every skill generation, regeneration, and evolution attempt that reaches a known skill name.
- **FR-002**: Reports MUST include skill name, lifecycle mode, candidate path when available, timestamp, final status, lifecycle stage results, and next-step guidance.
- **FR-003**: Reports for successful smoke tests MUST include the smoke-test request and output preview when available.
- **FR-004**: Reports for failed smoke tests MUST include the smoke-test request and failure reason.
- **FR-005**: Reports for regenerated or evolved skills MUST include approved baseline availability and rendered diff records for `SKILL.md` and `skill.py`.
- **FR-006**: Reports for evolved skills MUST include the failure context used for generation when available.
- **FR-007**: Report persistence MUST be file-backed and inspectable with ordinary text and JSON tooling.
- **FR-008**: Report persistence MUST NOT approve, load, execute, or otherwise change the existing trust boundary for proposed skills.
- **FR-009**: Report writing failures MUST be visible to the command caller but MUST NOT corrupt existing approved skill files.

### Key Entities

- **Lifecycle Report**: Durable record of a single lifecycle attempt, including metadata, stage results, smoke test, diffs, failure context, and next steps.
- **Lifecycle Stage Result**: One stage outcome from Critique, Generate, Validate, Test, or Propose.
- **Baseline Reference**: The approved baseline availability state used for candidate diffs.
- **Diff Record**: Rendered comparison for one artifact.
- **Failure Context**: The telemetry-backed failure details that triggered an evolution proposal.

## Success Criteria

### Measurable Outcomes

- **SC-001**: 100% of successful generate, regenerate, and evolve attempts leave a human-readable report in the relevant skill or candidate directory.
- **SC-002**: 100% of validation and smoke-test failures covered by automated tests leave a report that identifies the failed stage and reason.
- **SC-003**: Reviewers can locate the approval command and candidate path from the report without re-running generation.
- **SC-004**: Existing approval behavior remains unchanged, proven by the existing approval and generation test suite.

## Assumptions

- Reports are stored beside the proposed artifacts because reviewers already inspect `skills/<name>/` and `skills/<name>/.candidate/`.
- Markdown is the primary human-readable report format; JSON is retained as structured sidecar data for future CLI polish.
- Historical report indexing is out of scope for this issue; the latest report per candidate is sufficient for ISS-019.
