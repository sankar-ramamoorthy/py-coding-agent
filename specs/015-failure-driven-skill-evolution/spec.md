# Feature Specification: Failure-Driven Skill Evolution

**Feature Branch**: `[015-failure-driven-skill-evolution]`

**Created**: 2026-08-30

**Status**: Implemented

**Input**: User description: "File/spec/plan ISS-017 for failure-driven evolution as a separate M7 issue."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Propose a Fix From a Skill Failure (Priority: P1)

A user can take a real approved-skill failure and ask the agent to propose a revised skill using
the failure context.

**Why this priority**: This is the self-improving part of M7, but it must remain proposal-only so
failed skills never silently patch themselves.

**Independent Test**: Cause an approved skill to fail, request an evolution proposal, and confirm
the generated revision uses the failure context and remains proposed.

**Acceptance Scenarios**:

1. **Given** an approved skill fails during normal use, **When** the user requests a fix proposal,
   **Then** the system generates a proposed revision informed by the failure details.
2. **Given** a proposed revision is generated from a failure, **When** the lifecycle completes,
   **Then** the skill still requires explicit approval before normal execution.

---

### User Story 2 - Route Proposed Fixes Through the Lifecycle (Priority: P2)

A user sees that a failure-driven revision passed the same lifecycle checks as a newly generated
skill before review.

**Why this priority**: Failure context should improve generation input, not bypass critique,
validation, smoke testing, or approval.

**Independent Test**: Generate a failure-driven revision and confirm it runs through the
`ISS-015` lifecycle.

**Acceptance Scenarios**:

1. **Given** a failure-driven revision request, **When** the system proposes revised artifacts,
   **Then** the result includes critique, generation, validation, smoke-test, and propose stages.
2. **Given** the revised artifacts fail validation or smoke testing, **When** the lifecycle stops,
   **Then** the user sees the failed stage and no approval-ready revision is presented.

### Edge Cases

- The failed skill is no longer approved.
- Failure context is unavailable or too old.
- The failure came from disallowed tool access.
- The generated fix fails validation.
- The generated fix passes validation but fails smoke testing.
- Multiple failures exist for the same skill and the user requests evolution.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST let a user request a proposed revision for a skill based on a real
  recorded failure.
- **FR-002**: The proposed revision MUST include the failure details as generation context.
- **FR-003**: Failure-driven revision MUST re-enter the `ISS-015` lifecycle before proposal.
- **FR-004**: Failure-driven revision MUST NOT approve, ledger-record, or load itself
  automatically.
- **FR-005**: The system MUST explain when no usable failure context is available.
- **FR-006**: The system MUST preserve the original approved skill unless the user explicitly
  approves a replacement through the existing approval path.
- **FR-007**: The feature MUST NOT implement persistent lifecycle dashboards, CLI/UX polish,
  signed packages, or isolated-worker execution.

### Key Entities

- **Skill Failure Context**: The failure reason, request, skill name, provider/model context if
  available, and timing details used to inform a revision.
- **Evolution Proposal**: A proposed replacement or revision generated from failure context.
- **Lifecycle Result**: The `ISS-015` stage report for the proposed revision.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can generate a proposed revision from a captured skill failure without
  manually copying the failure text into a fresh skill request.
- **SC-002**: 100% of failure-driven revisions run through the same pre-approval lifecycle as new
  generated skills.
- **SC-003**: 100% of failure-driven revisions require explicit approval before normal execution.
- **SC-004**: Requests without usable failure context return a clear explanation instead of
  generating an unsupported revision.

## Assumptions

- `ISS-015` has been implemented.
- The existing telemetry/failure logging surface is enough to locate recent failure context or can
  be extended minimally inside this slice.
- Persistence/reporting polish and CLI/UX polish are separate issues per user direction.
