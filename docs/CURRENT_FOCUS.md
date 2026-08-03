# Current Focus

## Active branch
`fix-skill-tool-approval-gate` — implementation complete and verified against the real
running container, awaiting review before push/PR.

## What was just finished
`ISS-003`: skills and dynamic tools no longer execute code before approval. A separate,
tamper-evident approval ledger (content hash, not just an in-file status field) gates
skill execution; `/approve` re-validates current code; dynamic tools are off by default
via `ENABLE_DYNAMIC_TOOLS`; static safety checks run before any generated code can be
written to disk or executed. See `docs/SESSION_LOG.md`'s 2026-08-03 "Fix skill/dynamic-tool
approval gate" entry.

## Why
The 2026-08-02 audit's third critical finding (C-03) — confirmed live this session by
reproducing the actual bug (a proposed skill's module code executing at load time)
against the real, pre-fix code.

## Not being worked on right now (explicitly out of scope)
- `ISS-008` (full isolated-worker-with-RPC execution for skills/tools) — newly logged,
  the materially larger infrastructure item explicitly deferred from this fix
- `ISS-005` (pre-existing, unrelated test failures) — logged, not fixed
- `ISS-006` (pyyaml root dependency hygiene) — logged, not fixed
- Re-auditing the actual content quality of the 8 auto-seeded, already-approved skills

## Milestone note
With ISS-001 (C-01), ISS-002 (C-02), and ISS-003 (C-03) all resolved, every critical
finding from the original 2026-08-02 security audit has now been addressed.
