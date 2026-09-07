# Current Focus

## Active branch

`m8-provenance-planning`

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

All tracked pre-M8 issues are complete and merged to `main`. The repo is at a planning boundary:
M8 skill provenance/sharing is no longer assumed to be the automatic next milestone.

## Current planning direction

Evidence labels to preserve when discussing future work:

- IMPLEMENTED
- PLANNED
- PROPOSED
- EXPERIMENT
- LEARNING NOTE
- DEFERRED
- REJECTED

Current position:

- IMPLEMENTED: M6 Reliability Foundation is complete.
- IMPLEMENTED: M7 Skill Lifecycle Graph is complete.
- IMPLEMENTED: Pre-M8 work is complete.
- IMPLEMENTED: Current repo state is clean and validation was green at the last recorded
  full validation.
- PROPOSED: The next investigation should prioritize repo-local usability before assuming a new
  architecture milestone.

Preferred next sequence:

1. Repo-local usability
   - PROPOSED: Target normal interaction should be `cd <repo> && py-agent`.
   - PROPOSED: The current repository should become the workspace automatically.
   - PROPOSED: Normal use should not require running from the py-coding-agent source repo,
     manually passing paths, invoking internal modules, manually operating Docker, or
     understanding worker topology.
   - PROPOSED: Preferred architecture direction to investigate is a host-side CLI/control plane
     with Docker-backed execution hidden underneath it.
   - DEFERRED: Treat this as a direction to investigate, not implemented architecture.
2. Real-world dogfooding
   - EXPERIMENT: Once usability is adequate, use py-coding-agent on real bounded tasks in
     unrelated repositories.
   - LEARNING NOTE: Gather evidence about task success, awkwardness, failures, retries, skill
     usefulness, human intervention, state loss, and provider/model fit.
3. Evidence-driven next architecture
   - PROPOSED: Let observed failures determine whether durability/resume, observability, routing,
     stronger isolation, provenance/sharing, or another capability deserves the next milestone.
   - DEFERRED: Do not start provenance/sharing merely because it had previously been called M8.

Guiding principle:

`simple outside, disciplined inside`

`real usage -> observed failure -> justified architecture`

## Not being worked on right now

- M8 skill provenance/sharing remains a product-scope decision, not active implementation.
- No new issues, milestones, ADRs, Spec Kit plans, branches, or code changes are active from this
  note.

## Milestone note

M7 known core slices as of 2026-08-30:

- `ISS-015`: first lifecycle graph slice -- done.
- `ISS-016`: diff-on-regeneration -- done.
- `ISS-017`: failure-driven skill evolution -- done.
- `ISS-018`: persistence/reporting closeout -- done on branch `iss-018-lifecycle-reports`.
- `ISS-019`: CLI/UX review polish closeout -- done on branch `iss-019-lifecycle-cli-polish`.
- `ISS-008`: isolated-worker execution -- done on branch `iss-008-isolated-worker-execution`.
