# Current Focus

## Active branch

`implement-m7-skill-lifecycle`

## What was just finished

- `ISS-015` is implemented: skill generation reports
  `Critique -> Generate -> Validate -> Test(smoke run) -> Propose`.
- `ISS-016` is implemented: regenerating an existing skill writes a `.candidate`, shows separate
  `SKILL.md` and `skill.py` diffs against the approved baseline when available, and keeps approval
  manual.
- `ISS-017` is implemented: `/skill generate_skill --evolve <skill-name>` uses the latest
  actionable failed telemetry record as generation context, re-enters the lifecycle, and writes a
  proposed candidate.
- `ISS-018` and `ISS-019` are filed as separate M7 closeout issues, per user direction.

## Why

The known core M7 slices are complete on this branch. The remaining M7 closeout work is
tracked separately: `ISS-018` first for durable lifecycle state/reporting, then `ISS-019` for
CLI review polish.

## Not being worked on right now

- `ISS-008` (full isolated-worker-with-RPC execution for skills/tools) remains gated and
  deferred as an M8 prerequisite.
- `ISS-018` persistence/reporting polish is intentionally separate from the core M7 slices.
- `ISS-019` CLI/UX polish is intentionally separate from the core M7 slices.

## Milestone note

M7 known core slices as of 2026-08-30:

- `ISS-015`: first lifecycle graph slice -- done.
- `ISS-016`: diff-on-regeneration -- done.
- `ISS-017`: failure-driven skill evolution -- done.
- `ISS-018`: persistence/reporting closeout -- open.
- `ISS-019`: CLI/UX review polish closeout -- open.
