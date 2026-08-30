# Feature Specification: Skill Regeneration Diff

**Feature Branch**: `[014-skill-regeneration-diff]`

**Created**: 2026-08-30

**Status**: Implemented

**Input**: User description: "File/spec/plan ISS-016 for diff-on-regeneration as a separate M7 issue."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Review Changes Before Re-Approval (Priority: P1)

A user regenerating an existing skill can see what changed compared with the last approved
version before deciding whether to approve the regenerated version.

**Why this priority**: Regeneration currently risks replacing a durable reviewed skill with new
LLM output without an easy change review. Diff visibility is the core value of this slice.

**Independent Test**: Regenerate an existing approved skill and confirm the result includes a
diff between the regenerated artifacts and the last approved artifacts.

**Acceptance Scenarios**:

1. **Given** an approved skill with an approval ledger entry, **When** the user regenerates that
   skill, **Then** the result shows changed, added, and removed lines for the regenerated files.
2. **Given** a regenerated skill diff, **When** the user reviews the result, **Then** the skill
   remains proposed until the existing approval action is completed.

---

### User Story 2 - Handle Missing Baselines Clearly (Priority: P2)

A user receives a clear explanation when the system cannot produce a last-approved diff.

**Why this priority**: Not every skill has an available approved baseline; failure should be
explicit rather than silently omitting the review signal.

**Independent Test**: Attempt regeneration for a skill without a usable approved baseline and
confirm the output explains why no diff is available.

**Acceptance Scenarios**:

1. **Given** an existing skill without approved code, **When** the user regenerates it, **Then**
   the result states that no approved baseline exists.
2. **Given** an approved skill whose baseline cannot be recovered, **When** regeneration
   completes, **Then** the result warns that diff evidence is unavailable and still requires
   manual approval.

### Edge Cases

- The current file hash does not match the approval ledger.
- Only `SKILL.md` changes.
- Only `skill.py` changes.
- Both files are unchanged after regeneration.
- The approved baseline exists in git history but the working tree has unapproved edits.
- The regenerated output fails the `ISS-015` lifecycle before proposal.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support regenerating an existing skill without treating the result
  as approved.
- **FR-002**: The system MUST compare regenerated skill artifacts against the last approved
  baseline when that baseline is available.
- **FR-003**: The diff MUST identify changes separately for `SKILL.md` and `skill.py`.
- **FR-004**: The result MUST clearly state when no approved baseline is available.
- **FR-005**: The result MUST clearly state when regenerated artifacts are unchanged from the
  approved baseline.
- **FR-006**: The regenerated skill MUST pass the `ISS-015` lifecycle before diff review is
  presented as approval-ready.
- **FR-007**: Passing diff review MUST NOT approve, ledger-record, or load the regenerated skill.
- **FR-008**: The feature MUST NOT implement production-failure self-repair, signed packages, or
  isolated-worker execution.

### Key Entities

- **Approved Baseline**: The last artifact pair that the approval ledger recognizes as approved.
- **Regenerated Skill Candidate**: Newly generated `SKILL.md` and `skill.py` awaiting review.
- **Artifact Diff**: User-visible comparison between baseline and regenerated artifacts.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can see whether `SKILL.md`, `skill.py`, or both changed during regeneration.
- **SC-002**: 100% of regenerated skills still require explicit approval before normal execution.
- **SC-003**: 100% of regeneration attempts without a usable approved baseline report that fact.
- **SC-004**: A no-change regeneration clearly reports that no artifact changes were found.

## Assumptions

- `ISS-015` has been implemented before this slice.
- The approval ledger remains the authority for whether a skill is approved.
- Git history may help recover baselines, but this feature should degrade clearly if a baseline
  cannot be found.
