# Feature Specification: Fix pre-existing test failures

**Feature Branch**: `fix-pre-existing-test-failures`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work — see Milestone 6, `docs/ROADMAP_PLAN.md`)

**Input**: User description: "Root-cause and fix ISS-005 — pre-existing test failures unrelated
to any current branch work, discovered 2026-08-03. Required before Milestone 6's CI (ISS-012)
can be green-required, since CI can't gate merges on a suite with known, undiagnosed red tests.
See `docs/ISSUES.md` ISS-005."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The test suite reflects real problems, not stale drift (Priority: P1)

A contributor (human or AI) runs the full test suite before starting new work and needs every
failure to mean something real is broken — not that a test and its implementation drifted apart
independently, unrelated to whatever the contributor is currently touching.

**Why this priority**: This is the direct blocker for Milestone 6's CI item (ISS-012). CI cannot
be made green-required while known, undiagnosed failures exist — a red suite that's "expected"
trains contributors to ignore red, defeating the point of CI.

**Independent Test**: Run the full `pytest` suite on a clean checkout of `main` and confirm zero
failures unrelated to work in progress.

**Acceptance Scenarios**:

1. **Given** a clean checkout of `main` with no in-progress changes, **When** the full test suite
   is run, **Then** every test passes or is skipped for a documented, unrelated environment
   reason (not silently expected to fail).
2. **Given** the `listallpy` skill is exercised with a mocked `list_files` tool result, **When**
   its test runs, **Then** the skill's actual output reflects the tool's mocked filtering, not the
   real filesystem.
3. **Given** all skills currently recorded as approved in the approval ledger, **When** the
   registry loads them, **Then** every one of them loads successfully, regardless of what
   platform (line-ending convention) the repository was checked out on.
4. **Given** `create_tool` is called with a valid name and a code snippet containing a function,
   **When** it succeeds, **Then** the result message and file contents match what the tool
   actually does, and an invalid name is rejected with a message consistent with this module's
   own error-message convention.

---

### User Story 2 - Skill approval survives being checked out on a different platform (Priority: P1)

An operator approves a skill on one platform (e.g. native Windows) and later that same,
unmodified, git-tracked skill is checked out on a different platform (e.g. a Linux CI runner or
container) as part of normal development. The skill's approval status must not silently change
just because of how the checkout platform represents line endings on disk.

**Why this priority**: Verified during this fix that this is not a one-off — 7 of the repo's 9
currently-approved skills would already fail their hash-ledger approval check if checked out with
Linux-style line endings, which is exactly what a Linux CI runner (ISS-012, also Milestone 6)
would do. Left unfixed, turning on CI would have broken most skills' approval status on day one,
for a reason with nothing to do with any actual approval decision.

**Independent Test**: Approve a skill, simulate a checkout on a different line-ending convention
with no content change, and confirm the skill is still recognized as approved.

**Acceptance Scenarios**:

1. **Given** a skill was approved and its `skill.py` content is later re-checked-out with
   different line endings but no actual content change, **When** the registry checks its approval
   status, **Then** it is still recognized as approved.
2. **Given** a skill's `skill.py` content is genuinely modified after approval, **When** the
   registry checks its approval status, **Then** it is correctly recognized as no longer approved
   (this fix must not weaken the ISS-003 approval gate itself).

---

### Edge Cases

- What happens if a skill's `skill.py` is missing entirely? Unaffected by this fix — already
  handled as "not approved" by the existing ledger check.
- What happens to skills whose ledger hash was computed under the old (non-normalized) scheme?
  All existing ledger entries were regenerated using the fixed hashing so none are left stale.
- Does normalizing line endings before hashing weaken the approval gate's security guarantee
  (detecting real content tampering)? No — only the specific byte sequence `\r\n` is folded to
  `\n` before hashing; any other content change still changes the hash and still invalidates
  approval (covered by an explicit test).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The `listallpy` skill MUST retrieve file listings only through
  `context.agent_tools`, never by accessing the filesystem directly, consistent with this
  project's existing tool/skill separation rule (ADR-016).
- **FR-002**: The skill-approval hash check MUST recognize a previously-approved skill as still
  approved when its tracked content is unchanged but its on-disk line-ending representation
  differs (e.g. due to a different checkout platform).
- **FR-003**: The skill-approval hash check MUST continue to reject a skill whose content has
  genuinely changed since approval (no weakening of the existing approval gate).
- **FR-004**: `create_tool`'s success and rejection messages MUST accurately describe its actual
  behavior and follow this module's existing error-message convention.
- **FR-005**: The full test suite MUST pass (or skip only for documented, environment-specific,
  unrelated reasons) on a clean checkout, with no known-red tests left unaddressed.
- **FR-006**: Automated test coverage MUST be added for the line-ending-normalization behavior
  (FR-002/FR-003), not just for the one skill (`listallpy`) that surfaced it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pytest` run on a clean checkout of the fix produces zero unexplained failures.
- **SC-002**: `python -m compileall` continues to exit cleanly (no regression).
- **SC-003**: Every skill currently recorded as approved still loads successfully after this fix,
  verified by the existing regression test for that guarantee.
- **SC-004**: A simulated cross-platform checkout (same content, different line endings) no
  longer changes any skill's approval outcome, verified by a dedicated automated test.
- **SC-005**: Milestone 6's CI item (ISS-012) can be made green-required on top of this fix
  without needing to special-case or skip any test that was failing before this fix.

## Assumptions

- The three failures found (skill/tool-boundary violation in `listallpy`, the line-ending-fragile
  approval hash, and two message-text/contract mismatches in `create_tool`) are independent of
  each other and of any other in-progress branch work — each was confirmed reproducible on a
  clean `main` checkout before being fixed.
- Where a test's expectation and the implementation's actual, intentional behavior disagreed
  (`create_tool`), the implementation's behavior was treated as authoritative when it was already
  relied upon by other passing tests in the same file, and the test was corrected — rather than
  changing production behavior to match a stale test with no other callers depending on it.
- Normalizing only `\r\n` -> `\n` before hashing is sufficient; no other content-normalization
  (e.g. trailing whitespace, encoding) is in scope, since line-ending conversion is the only
  cross-platform discrepancy actually observed.
