# Research: Lifecycle CLI Review Polish

## Decision: Add `/skill review <name>`

**Rationale**: Review is distinct from running and approving. A dedicated command gives reviewers a predictable entry point without overloading `/skill help`.

**Alternatives considered**: Expanding `/skill help` to print full reports was rejected because help should remain focused on the approved or proposed skill spec.

## Decision: Render JSON first, Markdown fallback second

**Rationale**: JSON is stable and concise to summarize; Markdown fallback preserves usefulness if the structured file is missing or corrupt.

**Alternatives considered**: Parsing Markdown first was rejected because prose parsing is less stable for future CLI polish.

## Decision: Do not add global candidate index

**Rationale**: The current issue is about clear review UX around one skill at a time. A global index would duplicate `ISS-018` storage and increase synchronization risk.

**Alternatives considered**: Scanning all skill directories for candidates is useful for future work but not required to review a known candidate.
