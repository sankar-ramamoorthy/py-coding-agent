# Project Status

Snapshot of overall project state. Update at milestone boundaries, not every session —
for moment-to-moment state use `CURRENT_FOCUS.md` and `SESSION_LOG.md` instead.

## Current milestone
ms5-skills (skills layer, Spec Kit integration) is complete and in active use. Merged to
`main`: `kb-template`, `ollama-dual-backend`, `fix-workspace-sandbox` (PRs #79-81),
`fix-skill-tool-approval-gate` (ISS-003, PR #82), README/kb-template doc-drift cleanup
(PR #83), the py-coding-agent lifecycle one-pager + cross-project reference redaction
(PR #84), the `capture-brainstorm-note` skill plus filing/speccing ISS-009 (PR #85),
`fix-ollama-thinking-response` (ISS-009, PR #86), filing ISS-010 (PR #87) and ISS-011
(PR #88), and the `listallpy` skill — a live, real dogfood of the ISS-009 fix (PR #89).
No branch currently active; working tree is clean off `main`. See `docs/SESSION_LOG.md`
for full records.

## Known critical/open issues
See `docs/ISSUES.md` for the live register. As of 2026-08-05: all three original critical
audit findings (ISS-001/C-01, ISS-002/C-02, ISS-003/C-03) are fixed and merged, and ISS-009
(Ollama thinking-model empty response) is fixed and merged. Remaining open, none started:
`ISS-005` (pre-existing test failures, root cause not yet investigated), `ISS-006` (pyyaml
dependency hygiene), `ISS-008` (deferred isolated-worker execution project), `ISS-010`
(bare `/provider` falls through to the LLM), `ISS-011` (three `generate_skill`
output-quality gaps found dogfooding against `qwen2.5-coder:7b-instruct-q5_K_M`).

## Architecture references
- `docs/adr/` — standing architecture decisions (ADR-001 through ADR-019).
- `specs/` — Spec Kit per-feature plans.
- `AGENTS.md` / `.specify/memory/constitution.md` — operating constraints, kept in sync.
