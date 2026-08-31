# Feature Specification: Lifecycle CLI Review Polish

**Feature Branch**: `iss-019-lifecycle-cli-polish`

**Created**: 2026-08-31

**Status**: Draft

**Input**: User description: "ISS-019: polish CLI UX for lifecycle review. Improve /skill help, /skill list, generation output, candidate review, diff display, and /approve messaging around lifecycle proposals and candidates. Do this after ISS-018 so the CLI can display stable persisted lifecycle state."

## User Scenarios & Testing

### User Story 1 - Review Pending Candidate From CLI (Priority: P1)

A human reviewer can run one clear command to inspect the latest lifecycle report and candidate status for a skill before approval.

**Why this priority**: Candidate review is the core human approval path and should not require manually guessing file paths.

**Independent Test**: Create a skill candidate with a lifecycle report, run the review command, and verify the output includes status, candidate path, stages, smoke-test result, diffs, and approval command.

**Acceptance Scenarios**:

1. **Given** a skill has a `.candidate` report, **When** the reviewer runs the review command, **Then** the CLI shows the candidate path, lifecycle status, stage outcomes, diff summary, and approval command.
2. **Given** a proposed new skill has a lifecycle report at the skill root, **When** the reviewer runs the review command, **Then** the CLI shows the report summary and approval command.

---

### User Story 2 - Discover Review State In Existing Commands (Priority: P2)

A reviewer can see from `/skill list` and `/skill help <name>` whether a skill has a pending candidate and which review command to run.

**Why this priority**: Review state should be visible from commands users already know.

**Independent Test**: List and inspect a skill with a pending candidate and verify the output points to review and approval commands.

**Acceptance Scenarios**:

1. **Given** a skill has a pending candidate, **When** the user runs `/skill list`, **Then** that skill is marked as having a pending candidate.
2. **Given** a skill has a pending candidate, **When** the user runs `/skill help <name>`, **Then** the help output points to the candidate review command.

---

### User Story 3 - Approve With Clear Outcome (Priority: P3)

After approval, the CLI explains whether a candidate was promoted and where the retained lifecycle report lives.

**Why this priority**: Approval is the trust boundary, so the result should be explicit and auditable.

**Independent Test**: Approve a valid candidate and verify the success message states that a candidate was promoted, the skill is ready, and the report path is retained.

**Acceptance Scenarios**:

1. **Given** a valid pending candidate exists, **When** the reviewer approves it, **Then** the CLI states the candidate was promoted and names the retained lifecycle report path.
2. **Given** an invalid pending candidate exists, **When** the reviewer approves it, **Then** the CLI states validation failed and points back to review without overwriting the approved skill.

### Edge Cases

- If no lifecycle report exists, review output explains what is missing and still shows available skill status.
- If report JSON is corrupt, review output falls back to the Markdown report when available.
- Existing skill execution commands remain unchanged.
- Proposed and deprecated skills are not executed as part of review.

## Requirements

### Functional Requirements

- **FR-001**: The system MUST recognize `/skill review <skill-name>` as a special command.
- **FR-002**: The review command MUST summarize lifecycle report JSON when available.
- **FR-003**: The review command MUST include stage results, smoke-test result, diff availability, candidate path, status, and next approval command when present.
- **FR-004**: The review command MUST fall back to the Markdown lifecycle report when JSON is unavailable or unreadable.
- **FR-005**: `/skill list` MUST identify skills with pending candidates and point to the review command.
- **FR-006**: `/skill help <skill-name>` MUST identify pending candidates and point to the review command.
- **FR-007**: `/approve <skill-name>` success output MUST say when a candidate was promoted and identify the retained lifecycle report path when present.
- **FR-008**: `/approve <skill-name>` validation failure output MUST preserve existing files and direct the reviewer back to candidate review.
- **FR-009**: CLI review polish MUST NOT approve, load, or execute proposed skills.

### Key Entities

- **Review Summary**: CLI-rendered summary of a lifecycle report and candidate state.
- **Pending Candidate Indicator**: List/help marker showing that a candidate awaits review.
- **Approval Outcome Message**: Explicit message describing candidate promotion or rejection.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Reviewers can identify a pending candidate and the correct approval command from `/skill list` and `/skill help <name>`.
- **SC-002**: Reviewers can inspect lifecycle status, smoke-test result, diff summary, and candidate path with one review command.
- **SC-003**: Candidate approval messages explicitly state promotion status and retained report path.
- **SC-004**: Existing skill command tests and approval tests remain green.

## Assumptions

- The stable report files from `ISS-018` are the source of truth for review summaries.
- A new `/skill review <name>` command is acceptable because it is the smallest clear CLI surface for lifecycle review.
- Rich terminal formatting is out of scope; plain text output is sufficient.
