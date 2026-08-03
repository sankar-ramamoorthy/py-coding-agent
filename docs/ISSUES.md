# Issues Register

Lightweight issue tracker for py-coding-agent. Not a substitute for `docs/adr/` (standing
architecture decisions) or `specs/` (Spec Kit feature plans) — this is for tracking discrete,
open pieces of work and known problems across sessions.

## Fields
- **ID** — sequential, prefixed `ISS-NNN` (zero-padded, 3 digits, monotonically increasing, never reused)
- **Title** — short description
- **Status** — `open | in-progress | blocked | done | wontfix`
- **Branch** — branch working the issue, if any (`—` if none yet)
- **Source** — where it originated (e.g. link/reference to audit report, session, or requester)
- **Notes** — brief context, links to relevant files/ADRs

## Open / Tracked

| ID | Title | Status | Branch | Source | Notes |
|----|-------|--------|--------|--------|-------|
| ISS-001 | App fails to import/start (syntax errors) | in-progress | — | docs/project-audit-2026-08-02.md (C-01) | Commit `34e595e` ("fixed syntax errors and tested system") suggests this is already fixed. Re-verify with `python -m compileall` before closing. |
| ISS-002 | `/workspace` sandbox escape via path-check bypass | open | — | docs/project-audit-2026-08-02.md (C-02) | Path-check accepts a naive prefix match; `shell=True` and a rw compose mount also implicated. Not yet remediated. |
| ISS-003 | Skills/dynamic tools execute arbitrary code before approval | open | — | docs/project-audit-2026-08-02.md (C-03) | Approval enforcement happens after import/exec, not before. Not yet remediated. |
| ISS-004 | Add kb-template/ portable knowledge-base scaffold | in-progress | kb-template | 2026-08-03 session | Reusable YAML front-matter + Obsidian-markdown scaffold, extracted before further TradeForge-KB/AITrader-style drift accumulates. |

## Closed

(move rows here once `status: done`/`wontfix`, keep table for history)
