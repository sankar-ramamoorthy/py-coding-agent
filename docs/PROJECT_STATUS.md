# Project Status

Snapshot of overall project state. Update at milestone boundaries, not every session —
for moment-to-moment state use `CURRENT_FOCUS.md` and `SESSION_LOG.md` instead.

## Current milestone
ms5-skills (skills layer, Spec Kit integration). `kb-template`, `ollama-dual-backend`, and
`fix-workspace-sandbox` all merged to `main` (PRs #79, #80, #81). `fix-skill-tool-approval-gate`
(ISS-003, the pre-approval code execution finding) is implemented and verified against the
real running container, not yet pushed/merged. See `docs/SESSION_LOG.md` for full records
of all four.

## Known critical/open issues
See `docs/ISSUES.md` for the live register. As of 2026-08-03: all three original critical
audit findings (ISS-001/C-01, ISS-002/C-02, ISS-003/C-03) are fixed — ISS-003 pending
merge. Remaining open: `ISS-005`, `ISS-006` (minor, pre-existing), `ISS-008` (deferred
isolated-worker execution project).

## Architecture references
- `docs/adr/` — standing architecture decisions (ADR-001 through ADR-019).
- `specs/` — Spec Kit per-feature plans.
- `AGENTS.md` / `.specify/memory/constitution.md` — operating constraints, kept in sync.
