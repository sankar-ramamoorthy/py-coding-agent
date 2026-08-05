# Feature Specification: Fix bare `/provider` falling through to the LLM

**Feature Branch**: `fix-bare-provider-command`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work)

**Input**: User description: "Fix ISS-010 — typing bare `/provider` (no argument) in the CLI is
not recognized as a special command and gets sent to the LLM as a normal chat message instead of
showing usage, unlike `/provider <name>` or `/providers` which both work correctly. See
`docs/ISSUES.md` ISS-010."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Typing `/provider` alone shows usage instead of confusing the LLM (Priority: P1)

An operator forgets the required argument and types `/provider` alone in the CLI, expecting
either the current provider info or a usage hint — the same kind of immediate, deterministic
feedback every other malformed command in this CLI already gives.

**Why this priority**: This is the concretely reported, reproducing bug — confirmed live: bare
`/provider` produced an LLM reply asking what "provider" meant, instead of the CLI's own usage
message.

**Independent Test**: Type `/provider` alone and confirm a `Usage: /provider <provider> [model]`
response is returned directly by the CLI, without an LLM call.

**Acceptance Scenarios**:

1. **Given** the CLI is running, **When** the user types `/provider` with no argument, **Then**
   the CLI returns `Usage: /provider <provider> [model]` directly, with no LLM call made.
2. **Given** the CLI is running, **When** the user types `/provider <name>` or
   `/provider <name> <model>`, **Then** behavior is unchanged from before this fix (no
   regression).
3. **Given** the CLI is running, **When** the user types `/providers` (plural), **Then** it is
   still handled by its own existing branch, unaffected by this fix.

### Edge Cases

- Does `/provider` with trailing whitespace only (`"/provider "`) still work? Yes — unaffected,
  already handled by the existing `text.startswith("/provider ")` branch before this fix, which
  already returned the same usage message for that case.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The CLI MUST recognize bare `/provider` (exact string, no argument) as a special
  command, not a message to forward to the LLM.
- **FR-002**: The CLI MUST respond to bare `/provider` with the same usage message already used
  for `/provider ` (trailing space, no argument): `Usage: /provider <provider> [model]`.
- **FR-003**: The fix MUST NOT change behavior for `/provider <name>`, `/provider <name> <model>`,
  or `/providers`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Typing `/provider` alone returns the usage message directly, with zero LLM calls.
- **SC-002**: Existing provider-switching and `/providers` behavior is unchanged, confirmed by
  automated tests covering all four input shapes (bare, trailing-space-only, valid argument,
  plural).

## Assumptions

- No other special command in this CLI has the same "requires a trailing space to be recognized"
  gap — this fix is scoped to `/provider` only, since that's the one concretely reported.
