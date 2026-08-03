# Current Focus

## Active branch
`ollama-dual-backend` — implementation complete and verified against real backends,
awaiting review before push/PR.

## What was just finished
`ISS-007`: dual Ollama backend selection (local laptop + remote GPU desktop over
Tailscale), with the remote backend preferred by default, automatic fallback to local,
explicit override for either, and runtime model switching. See `docs/SESSION_LOG.md`'s
2026-08-03 "Dual Ollama backend selection" entry for the full completion report.

## Why
The user's local machine is too slow for practical inference; a separate GPU-equipped
desktop is available but not always on. This lets py-coding-agent use whichever backend
is actually up, without manual reconfiguration, while still allowing explicit control.

## Not being worked on right now (explicitly out of scope)
- ISS-002 / ISS-003 (sandbox/execution security issues, formerly audit C-02/C-03) — still
  not started, per the user's original "even before fixing C-01 through C-03" framing
- ISS-005 (pre-existing, unrelated test failures) — logged, not fixed
- ISS-006 (pyyaml root dependency hygiene) — logged, not fixed
- Wiring the LiteLLM path into dual-backend selection (out of scope for ISS-007, unrelated)
- Any UI/rendering for backend status
