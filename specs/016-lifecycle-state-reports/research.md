# Research: Lifecycle State Reports

## Decision: Store reports next to candidate artifacts

**Rationale**: Reviewers already inspect `skills/<name>/` for new proposed skills and `skills/<name>/.candidate/` for regenerated or evolved skills. Co-locating `lifecycle_report.md` and `lifecycle_report.json` keeps the review context with the files being reviewed and avoids a new index or service.

**Alternatives considered**: A global `telemetry/` report index was rejected because telemetry is operational data and ignored by Git. A dashboard was rejected because ISS-018 explicitly scopes reporting to lightweight file-backed state.

## Decision: Persist both Markdown and JSON

**Rationale**: Markdown gives human reviewers an inspectable report in the terminal or editor. JSON gives ISS-019 a stable structured source for CLI display without reparsing terminal text.

**Alternatives considered**: Markdown only was simpler but would force later CLI polish to parse prose. JSON only was inspectable but less readable during manual review.

## Decision: Report write failures are surfaced, not fatal

**Rationale**: Report persistence should not approve or load a skill, and should not corrupt existing approved files. If report writing fails, the command should tell the caller while preserving the current lifecycle outcome.

**Alternatives considered**: Treating report write failure as a lifecycle failure was rejected because it would conflate candidate validity with documentation persistence.
