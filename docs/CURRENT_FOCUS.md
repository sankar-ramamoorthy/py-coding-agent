# Current Focus

## Active branch
`fix-workspace-sandbox` — implementation complete and verified against the real running
container, awaiting review before push/PR.

## What was just finished
`ISS-002`: the `/workspace` sandbox escape (audit finding C-02) is fixed. Real path
containment replaces the string-prefix bug, a deliberate empty-by-default
`ADDITIONAL_ALLOWED_PATHS` allowlist exists for granting extra access on purpose, the shell
tool is now an explicit opt-in with a timeout, and the dev container's source mount is
read-only. See `docs/SESSION_LOG.md`'s 2026-08-03 "Fix workspace sandbox escape" entry.

## Why
The 2026-08-02 security audit found the claimed workspace sandbox didn't actually hold —
confirmed live during this session by reproducing both bugs against the real, pre-fix code.

## Not being worked on right now (explicitly out of scope)
- ISS-003 (skills/dynamic tools executing code before approval, audit C-03) — the last of
  the three original critical findings still open
- ISS-005 (pre-existing, unrelated test failures) — logged, not fixed
- ISS-006 (pyyaml root dependency hygiene) — logged, not fixed
- True OS-level shell content sandboxing (separate restricted container, seccomp) —
  explicitly deferred, materially larger project
