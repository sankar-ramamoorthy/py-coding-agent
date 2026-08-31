# Project Status

Snapshot of overall project state. Update at milestone boundaries, not every session -- for
moment-to-moment state use `CURRENT_FOCUS.md` and `SESSION_LOG.md` instead.

## Current milestone

Milestone 6 (Reliability Foundation) is complete. It closed `ISS-005` through `ISS-006` and
`ISS-010` through `ISS-014`, including the green test baseline, direct `pyyaml` dependency,
bare `/provider` handling, `generate_skill` quality fixes, minimal CI, per-run skill telemetry,
and the model/task fitness check.

Milestone 7 (Skill Lifecycle Graph) core scope is complete and merged: `ISS-015` implemented
the first lifecycle slice, `ISS-016` implemented diff-on-regeneration, and `ISS-017`
implemented failure-driven skill evolution. `ISS-018` is complete on branch
`iss-018-lifecycle-reports`, adding durable Markdown and JSON lifecycle reports for generated,
regenerated, evolved, and failed skill candidate attempts. The remaining M7 closeout item is
`ISS-019` CLI/UX polish.

## Known critical/open issues

See `docs/ISSUES.md` for the live register. As of 2026-08-31, all M5 and M6 issues are closed.
Open tracked work:

- `ISS-008` (Gated / M8 prerequisite): full isolated-worker execution for skills/dynamic tools.
- `ISS-019` (M7 closeout): polish CLI UX for lifecycle review.

## Architecture references

- `docs/adr/` -- standing architecture decisions (ADR-001 through ADR-019).
- `specs/` -- Spec Kit per-feature plans.
- `AGENTS.md` / `.specify/memory/constitution.md` -- operating constraints, kept in sync.
