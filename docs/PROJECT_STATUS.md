# Project Status

Snapshot of overall project state. Update at milestone boundaries, not every session —
for moment-to-moment state use `CURRENT_FOCUS.md` and `SESSION_LOG.md` instead.

## Current milestone
ms5-skills (skills layer, Spec Kit integration) — `kb-template` branch's increment
(portable knowledge-base scaffold + process-doc bootstrap) is implemented and verified,
not yet pushed/merged. See `docs/SESSION_LOG.md` (2026-08-03 entry) for the full record.

## Known critical/open issues
See `docs/ISSUES.md` for the live register. As of 2026-08-03: the sandbox escape
(ISS-002) and pre-approval arbitrary code execution (ISS-003) are open and unresolved —
treat as blocking for anything touching `py_mono/tools/`, sandbox path checks, or
skill/dynamic-tool loading.

## Architecture references
- `docs/adr/` — standing architecture decisions (ADR-001 through ADR-019).
- `specs/` — Spec Kit per-feature plans.
- `AGENTS.md` / `.specify/memory/constitution.md` — operating constraints, kept in sync.
