# Current Focus

## Active branch

`iss-018-lifecycle-reports`

## What was just finished

- `ISS-015` is implemented: skill generation reports
  `Critique -> Generate -> Validate -> Test(smoke run) -> Propose`.
- `ISS-016` is implemented: regenerating an existing skill writes a `.candidate`, shows separate
  `SKILL.md` and `skill.py` diffs against the approved baseline when available, and keeps approval
  manual.
- `ISS-017` is implemented: `/skill generate_skill --evolve <skill-name>` uses the latest
  actionable failed telemetry record as generation context, re-enters the lifecycle, and writes a
  proposed candidate.
- M7 core was committed and merged to `main` in commit `5113903`.
- `ISS-018` is implemented on this branch: generated, regenerated, evolved, and failed lifecycle
  attempts now write durable Markdown and JSON lifecycle reports next to the proposed artifacts.

## Why

The first M7 closeout item is complete on this branch. The remaining pre-M8 order is `ISS-019`
for CLI review polish, then `ISS-008` for isolated-worker execution.

## Not being worked on right now

- `ISS-008` (full isolated-worker-with-RPC execution for skills/tools) remains gated and
  deferred as an M8 prerequisite.
- `ISS-019` CLI/UX polish is intentionally separate from the core M7 slices.

## Milestone note

M7 known core slices as of 2026-08-30:

- `ISS-015`: first lifecycle graph slice -- done.
- `ISS-016`: diff-on-regeneration -- done.
- `ISS-017`: failure-driven skill evolution -- done.
- `ISS-018`: persistence/reporting closeout -- done on branch `iss-018-lifecycle-reports`.
- `ISS-019`: CLI/UX review polish closeout -- open.
