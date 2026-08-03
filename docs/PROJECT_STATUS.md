# Project Status

Snapshot of overall project state. Update at milestone boundaries, not every session —
for moment-to-moment state use `CURRENT_FOCUS.md` and `SESSION_LOG.md` instead.

## Current milestone
ms5-skills (skills layer, Spec Kit integration). `kb-template` and `ollama-dual-backend`
both merged to `main` (PRs #79, #80). `fix-workspace-sandbox` (ISS-002, the workspace
sandbox escape) is implemented and verified against the real running container, not yet
pushed/merged. See `docs/SESSION_LOG.md` for full records of all three.

## Known critical/open issues
See `docs/ISSUES.md` for the live register. As of 2026-08-03: ISS-002 (sandbox escape) is
fixed, pending merge. ISS-003 (pre-approval arbitrary code execution) remains open and
unresolved — treat as blocking for anything touching skill/dynamic-tool loading.

## Architecture references
- `docs/adr/` — standing architecture decisions (ADR-001 through ADR-019).
- `specs/` — Spec Kit per-feature plans.
- `AGENTS.md` / `.specify/memory/constitution.md` — operating constraints, kept in sync.
