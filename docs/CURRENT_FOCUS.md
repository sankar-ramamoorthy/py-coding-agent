# Current Focus

## Active branch
None — all recent work merged to `main`, working tree clean. Session moved from
implementation into higher-level roadmap/product review (see below).

## What was just finished
- `ISS-009` (Ollama thinking-model empty response) — fixed and merged (PR #86). See
  `docs/SESSION_LOG.md`'s 2026-08-05 entry for the full empirical record.
- Live dogfood of that fix: generated and approved a real skill (`listallpy`) against a
  newly-configured model (`qwen2.5-coder:7b-instruct-q5_K_M`) — confirmed working
  end-to-end (PR #89).
- That dogfood run surfaced two more findings, filed but not fixed: `ISS-010` (bare
  `/provider` falls through to the LLM instead of showing usage, PR #87) and `ISS-011`
  (three `generate_skill` output-quality gaps — asymmetric fence-stripping, a leaked
  prompt template line, and a possible CPU-bound/unoffloaded inference signal, PR #88).
- Compiled a consolidated high-level roadmap across `README.md` milestones,
  `docs/ISSUES.md`, and `docs/NEXT_ACTIONS.md`, and started a product-level (not just
  backlog-level) review of where to invest next.

## Why
User wanted a clear picture of "what are all the TODOs" across the project, then asked
for a product-manager-level pass on top of that — not just the existing backlog, but
what actually most improves the product next, informed by real friction hit this session
(slow/unreliable local-model calls, generation-quality gaps, no CI, sparse test coverage).

## Not being worked on right now (explicitly out of scope)
- `ISS-008` (full isolated-worker-with-RPC execution for skills/tools) — deferred,
  materially larger infrastructure item
- `ISS-005` (pre-existing, unrelated test failures) — logged, root cause not yet
  investigated
- `ISS-006` (pyyaml root dependency hygiene) — logged, not fixed
- `ISS-010`, `ISS-011` — filed this session, explicitly deferred to Spec Kit, not fixed
- Swapping `OLLAMA_REMOTE_MODEL`/`OLLAMA_LOCAL_MODEL` away from thinking-capable models —
  user has started manually testing `qwen2.5-coder:7b-instruct-q5_K_M`; no default change
  made yet.

## Milestone note
All three original critical audit findings (ISS-001/002/003) plus ISS-009 are fixed and
merged. Five issues remain open, none started: two small/well-scoped (`ISS-010`,
`ISS-006`), one needing investigation before it's scoped (`ISS-005`), one large and
deliberately deferred (`ISS-008`), one small-multi-part (`ISS-011`). Milestone 4
(Documentation, full workflow testing, packaging) has never been started — M5 shipped
ahead of it, and there is currently no CI/pre-commit enforcement anywhere in the repo.
