# Project Status

Snapshot of overall project state. Update at milestone boundaries, not every session —
for moment-to-moment state use `CURRENT_FOCUS.md` and `SESSION_LOG.md` instead.

## Current milestone
ms5-skills (skills layer, Spec Kit integration). `kb-template` (portable knowledge-base
scaffold) merged to `main` via PR #79. `ollama-dual-backend` (local/remote Ollama
selection, ISS-007) is implemented and verified against real backends, not yet
pushed/merged. See `docs/SESSION_LOG.md` for full records of both.

## Known critical/open issues
See `docs/ISSUES.md` for the live register. As of 2026-08-03: the sandbox escape
(ISS-002) and pre-approval arbitrary code execution (ISS-003) are open and unresolved —
treat as blocking for anything touching `py_mono/tools/`, sandbox path checks, or
skill/dynamic-tool loading.

## Architecture references
- `docs/adr/` — standing architecture decisions (ADR-001 through ADR-019).
- `specs/` — Spec Kit per-feature plans.
- `AGENTS.md` / `.specify/memory/constitution.md` — operating constraints, kept in sync.
