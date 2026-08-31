# Current Focus

## Active branch

`iss-008-isolated-worker-execution`

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
- `ISS-019` is implemented on this branch: `/skill review <name>` summarizes lifecycle reports,
  `/skill list` and `/skill help <name>` surface pending candidates, generation output points to
  review, and `/approve` explains candidate promotion/rejection.
- `ISS-008` is implemented on this branch: approved skills load as metadata proxies and execute
  in subprocess workers; worker skills use parent-enforced JSON-line RPC for tools; dynamic tools
  load from static metadata and execute in subprocess workers.

## Why

All tracked pre-M8 issues are complete on this branch. The next decision is whether to start M8
skill provenance/sharing.

## Not being worked on right now

- M8 skill provenance/sharing remains a product-scope decision, not active implementation.

## Milestone note

M7 known core slices as of 2026-08-30:

- `ISS-015`: first lifecycle graph slice -- done.
- `ISS-016`: diff-on-regeneration -- done.
- `ISS-017`: failure-driven skill evolution -- done.
- `ISS-018`: persistence/reporting closeout -- done on branch `iss-018-lifecycle-reports`.
- `ISS-019`: CLI/UX review polish closeout -- done on branch `iss-019-lifecycle-cli-polish`.
- `ISS-008`: isolated-worker execution -- done on branch `iss-008-isolated-worker-execution`.
