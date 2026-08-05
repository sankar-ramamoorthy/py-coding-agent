# Feature Specification: Lightweight per-skill-run telemetry log

**Feature Branch**: `add-skill-run-telemetry`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work)

**Input**: User description: "Add ISS-013 — a flat per-run log (skill, provider, model,
duration, success) recorded every time a skill runs. Milestone 6's model/task fitness check
(ISS-014) can't exist without this data source; Milestone 7's failure-driven evolution extends
the same log rather than building a second one. See docs/ROADMAP_PLAN.md Milestone 6 and
docs/ISSUES.md ISS-013."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every skill run leaves a record usable for later analysis (Priority: P1)

An operator (or a future feature like the model/task fitness check) wants to know, after the
fact, which skill ran, with which provider/model, how long it took, and whether it succeeded —
without adding per-feature logging to every skill individually.

**Why this priority**: This is a hard blocker for `ISS-014` — the fitness check has no data
source without it — and the only item in Milestone 6 with a direct downstream dependent.

**Independent Test**: Run an approved skill through the normal execution path and confirm a
telemetry record appears with the expected fields.

**Acceptance Scenarios**:

1. **Given** an approved skill is run through `run_skill_safe`, **When** it completes
   successfully, **Then** exactly one telemetry record is appended containing the skill name,
   active provider, active model, duration in milliseconds, and `success: true`.
2. **Given** a skill's execution raises an exception, **When** `run_skill_safe` re-raises it,
   **Then** a telemetry record is still appended with `success: false` (a failure must not be
   silently unlogged).
3. **Given** no session manager is available (e.g. a test harness constructing `SkillContext`
   directly), **When** a skill runs, **Then** telemetry is still recorded, with provider/model
   recorded as `<unknown>` rather than the run itself failing.
4. **Given** the telemetry log file or its parent directory doesn't exist yet, **When** the
   first record is written, **Then** the directory is created automatically.

### Edge Cases

- What happens if the telemetry write itself fails (e.g. read-only filesystem)? Must not break
  skill execution — the write failure is logged as a warning and swallowed, never re-raised.
- What happens if the log file has a corrupt line (e.g. from a crash mid-write)? Reading the log
  must skip the corrupt line rather than fail the entire read.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST record one telemetry entry per skill run, containing: skill name,
  provider, model, duration in milliseconds, success flag, and a timestamp.
- **FR-002**: Telemetry MUST be recorded for both successful and failed skill runs.
- **FR-003**: A telemetry write failure MUST NOT propagate as an exception that breaks skill
  execution.
- **FR-004**: The log format MUST be append-friendly (one JSON object per line) so it can grow
  without rewriting the whole file.
- **FR-005**: A read helper MUST be provided that tolerates corrupt lines rather than failing
  the entire read.
- **FR-006**: The log location MUST be excluded from version control (operational data, not
  source), following this repo's existing pattern for other generated runtime directories
  (`workspace/`, `dynamic_tools/`).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Running any approved skill produces exactly one new telemetry record.
- **SC-002**: A failed skill run still produces a telemetry record (verified by an automated
  test using a skill that deliberately raises).
- **SC-003**: `ISS-014` (model/task fitness check) can consume this log directly as its data
  source with no further plumbing.

## Assumptions

- A flat, single JSONL file is sufficient for this milestone's scope — no rotation, size
  limits, or database backing is needed yet. Milestone 7 may extend this same file/format
  further; it is not expected to need a different storage mechanism to do so.
- Recording telemetry inside `run_skill_safe` (the single existing execution chokepoint for all
  skill runs, already responsible for approval and tool-access enforcement) is sufficient
  coverage — no additional instrumentation is needed at other call sites.
