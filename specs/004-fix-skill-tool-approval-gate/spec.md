# Feature Specification: Fix Skill/Tool Approval Gate

**Feature Branch**: `fix-skill-tool-approval-gate`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Fix skills and dynamically-generated tools so that a proposed skill or an auto-generated tool's own code is never run before an explicit, human approval decision has been made for it. Approval must re-check current implementation for known-unsafe patterns at approval time, and must be recorded separately from the artifact being approved so a later content change invalidates it until renewed. Auto-generated tools must gain a default-off gate plus a mandatory safety check before code is even written to disk. Existing approved skills must keep working without individual manual re-review."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A proposed skill's code never runs before approval (Priority: P1)

Whenever the system starts up or rescans available skills, a skill that hasn't been
explicitly approved has its description and status still visible and inspectable, but its
actual implementation code does not run — not even once, not even briefly, merely because
it was discovered.

**Why this priority**: This is the concretely demonstrated bug — everything else in this
feature builds on or hardens this core guarantee.

**Independent Test**: Place a not-yet-approved skill's implementation where the system
would normally discover it, with an observable side effect at the top of its code. Start
the system / trigger a rescan. Confirm the side effect never occurs. Confirm the skill is
still listed as discoverable (name, description, status visible).

**Acceptance Scenarios**:

1. **Given** a skill that has not been approved, **When** the system starts or rescans
   available skills, **Then** that skill's implementation code does not execute.
2. **Given** a skill that has not been approved, **When** its metadata is examined,
   **Then** its name, description, and status remain visible and inspectable.
3. **Given** a skill that has already been approved, **When** the system starts or
   rescans, **Then** its implementation code executes normally, exactly as it does today.

---

### User Story 2 - Approval re-validates current content and expires on later changes (Priority: P2)

Approving a skill checks its *current* implementation for known-unsafe patterns at the
moment approval is granted — not only whatever was reviewed when it was first written.
Approval is recorded separately from the skill's own files, so if the implementation
changes afterward, the approval no longer applies until it's explicitly renewed — a change
and its approval can't be silently bundled into the same edit.

**Why this priority**: Builds directly on User Story 1 — it closes the follow-on question
"once something is approved, can that approval be trusted going forward?"

**Independent Test**: Attempt to approve a skill whose current implementation contains a
known-unsafe pattern — confirm the approval is refused and the skill remains non-executing.
Approve a clean skill, then modify its implementation afterward — confirm it reverts to
non-executing until approved again.

**Acceptance Scenarios**:

1. **Given** a skill whose current implementation contains a known-unsafe pattern, **When**
   approval is attempted, **Then** the approval is refused and the skill remains
   unapproved and non-executing.
2. **Given** a skill with a clean implementation, **When** approval is granted, **Then**
   its implementation begins executing normally.
3. **Given** an approved skill whose implementation is modified afterward, **When** the
   system next loads or rescans it, **Then** it is no longer treated as approved until
   explicitly re-approved.
4. **Given** all skills that were already approved before this feature existed, **When**
   the system is upgraded to include this feature, **Then** they continue to load and run
   without requiring an individual, manual re-review from the operator.

---

### User Story 3 - Auto-generated tools default to not running automatically (Priority: P3)

Automatically generated tools — which today have no approval concept at all — do not
execute merely by being created. An operator must explicitly turn on the capability that
allows them to run at all.

**Why this priority**: Independent of Stories 1–2 (a separate code path, no shared
mechanism), but the same category of gap — closing it completes the fix's coverage of both
places arbitrary code could run unapproved.

**Independent Test**: With the capability in its default state, generate a tool and attempt
to make it available for use. Confirm it does not execute. Explicitly turn the capability
on. Confirm a generated tool now executes normally.

**Acceptance Scenarios**:

1. **Given** the system in its default configuration, **When** an auto-generated tool is
   created and the system attempts to make tools available, **Then** that tool's code does
   not execute.
2. **Given** an operator has explicitly enabled the capability, **When** an auto-generated
   tool is created and the system attempts to make tools available, **Then** it executes
   normally.

---

### User Story 4 - Generated tool code is safety-checked before it can exist at all (Priority: P4)

Before newly generated tool code is written to disk (and therefore becomes something that
could ever execute, now or later, regardless of the availability toggle in User Story 3),
it's checked for known-unsafe patterns. Code that fails this check is never written.

**Why this priority**: A defense-in-depth layer, independent of Story 3's toggle — even if
the toggle is later turned on, code that was never allowed to be written can never run.

**Independent Test**: Attempt to generate a tool whose code contains a known-unsafe
pattern. Confirm no file is created and a clear refusal is returned. Attempt to generate a
tool with clean code. Confirm it is written successfully.

**Acceptance Scenarios**:

1. **Given** generated tool code containing a known-unsafe pattern, **When** an attempt is
   made to persist it, **Then** nothing is written and a clear refusal is returned.
2. **Given** generated tool code with no known-unsafe pattern, **When** an attempt is made
   to persist it, **Then** it is written successfully.

---

### Edge Cases

- What happens to a not-yet-approved skill's tool-access permissions, since it never runs?
  Not applicable — a skill that never executes has no occasion to access any tool. This
  feature does not change how an *already-running, already-approved* skill's own tool
  access is constrained (that existing mechanism is separate and unaffected).
- What happens if approval is attempted on a skill with no implementation code at all
  (metadata only)? Out of scope for a code-safety check — there's nothing to validate;
  existing metadata-only handling is unaffected.
- What happens to the tool-call dispatch mechanism itself (how a tool call is routed to a
  loaded tool)? Unchanged — this feature only affects what gets loaded and when, not how an
  already-loaded, already-approved capability is invoked.
- What happens to a skill approved before this feature existed, if its implementation is
  edited for the first time *after* the feature ships? Same as any post-approval edit
  (Story 2, Scenario 3) — it reverts to non-executing until explicitly re-approved.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST NOT execute a skill's implementation code merely because it
  was discovered during startup or a rescan — only an approved skill's code may execute.
- **FR-002**: A not-yet-approved skill's name, description, and status MUST remain visible
  and inspectable even though its implementation does not execute.
- **FR-003**: Approving a skill MUST check its current implementation for known-unsafe
  patterns at the moment approval is granted; approval MUST be refused if any are found,
  and the skill MUST remain unapproved and non-executing.
- **FR-004**: Approval MUST be recorded in a way that is distinct from the skill's own
  implementation file(s) — not solely a field that lives inside the artifact being approved.
- **FR-005**: If an approved skill's implementation changes after approval, the system MUST
  no longer treat it as approved until it is explicitly re-approved.
- **FR-006**: Skills already approved before this feature exists MUST continue to load and
  run without requiring an individual, manual re-review from the operator.
- **FR-007**: Automatically generated tools MUST NOT execute unless an operator has
  explicitly enabled that capability; the default state MUST be disabled.
- **FR-008**: Newly generated tool code MUST be checked for known-unsafe patterns before it
  is written to disk; code that fails this check MUST NOT be persisted.
- **FR-009**: This feature MUST NOT change what an already-running, already-approved
  skill's own tool access is permitted to do.
- **FR-010**: This feature MUST NOT change the mechanism by which a loaded, available
  tool's calls are dispatched — only what gets loaded and when.

### Key Entities

- **Skill approval record**: a record, separate from a skill's own implementation file,
  associating a skill with the specific version of its implementation that was reviewed and
  approved. Invalidated when the implementation changes.
- **Skill**: has a name, description, an approval state, and an implementation. The
  implementation only executes when the current approval record matches the current
  implementation.
- **Generated tool availability toggle**: an operator-controlled setting determining whether
  auto-generated tools may execute at all. Disabled by default.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In 100% of tested cases, a not-yet-approved skill's implementation does not
  execute at startup or rescan, while its metadata remains inspectable.
- **SC-002**: In 100% of tested cases, approving a skill with a known-unsafe implementation
  is refused, and approving a clean one succeeds and results in normal execution.
- **SC-003**: In 100% of tested cases, modifying an approved skill's implementation after
  approval causes it to stop executing until explicitly re-approved.
- **SC-004**: 100% of skills already approved before this feature ships continue to load
  and run without any individual manual action from the operator.
- **SC-005**: With the generated-tool capability in its default state, 0% of auto-generated
  tools execute; after explicit enablement, they execute normally.
- **SC-006**: In 100% of tested cases, generated tool code containing a known-unsafe
  pattern is never written to disk.

## Assumptions

- "Known-unsafe pattern" refers to the same class of static, non-executing safety checks
  already used elsewhere in this system for reviewing generated code — this feature applies
  that existing class of check at new points in time (approval, generation), it does not
  invent a new definition of what counts as unsafe.
- Skills already approved before this feature ships are trusted at their current state as a
  one-time, automatic transition — this is explicitly not equivalent to a genuine review of
  their content, and should remain distinguishable from a real approval event if ever
  audited.
- Building a fully isolated execution environment for skills or tools is a separate, larger
  undertaking, explicitly out of scope here — this feature is about *whether and when* code
  is allowed to run, not about *containing* what already-approved code can do once running.
- Re-auditing the actual content quality of already-approved skills is out of scope — only
  whether their approvals remain recognized is addressed.
