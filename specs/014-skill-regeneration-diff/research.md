# Research: Skill Regeneration Diff

## Decision: Treat the approval ledger as baseline authority

**Rationale**: The ledger is already the source of truth for approved executable skill code. A
diff against any other baseline would blur the review boundary.

**Alternatives considered**:
- Compare against current working-tree files only: rejected because they may contain unapproved
  edits.
- Compare against the most recent git version only: useful fallback, but not sufficient unless it
  can be tied to the approved hash.

## Decision: Make missing baselines explicit

**Rationale**: If an approved baseline cannot be recovered, the user should know the diff signal
is unavailable. Silent omission would make regeneration look safer than it is.

**Alternatives considered**:
- Block all regeneration without a diff: rejected because manual review can still proceed if the
  output clearly states the missing baseline.

## Decision: Keep regeneration output proposed

**Rationale**: Diff review is evidence for the human, not a substitute for approval. This
preserves M5/M6 trust boundaries.

**Alternatives considered**:
- Auto-approve no-change regenerations: rejected because approval remains an explicit action.
