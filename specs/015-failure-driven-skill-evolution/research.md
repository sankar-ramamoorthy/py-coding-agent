# Research: Failure-Driven Skill Evolution

## Decision: Proposal-only evolution

**Rationale**: A skill failure is useful evidence for a better prompt, not permission to modify
approved behavior. The existing approval boundary must remain intact.

**Alternatives considered**:
- Automatic self-repair: rejected because it bypasses human review.
- Manual copy/paste into new generation: rejected because M7 should make failure context usable
  as product behavior.

## Decision: Reuse the `ISS-015` lifecycle

**Rationale**: Failure-driven revisions should be subject to the same critique, validation,
smoke-test, and proposal checks as new skills.

**Alternatives considered**:
- Special evolution-only checks: rejected because they would duplicate lifecycle logic and create
  a second review path.

## Decision: Extend failure context minimally only if needed

**Rationale**: M6 already added telemetry. This slice should use existing records first and only
add fields needed to make a failure actionable.

**Alternatives considered**:
- Dedicated persistence/reporting layer: rejected because the user explicitly split persistence
  reporting into a separate issue.
