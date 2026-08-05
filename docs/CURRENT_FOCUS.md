# Current Focus

## Active branch
`fix-ollama-thinking-response` — implementation complete, tested against real Ollama
servers, awaiting review before push/PR.

## What was just finished
`ISS-009`: `OllamaProvider.generate()` sent no `think`/`num_predict`/`num_ctx`, so a
thinking-capable Ollama model could exhaust its entire response budget on internal
reasoning and return empty content (`done_reason: "length"`). Fixed with two defenses,
both validated against real Ollama servers rather than assumed: `think: false` by default
(`OLLAMA_ENABLE_THINKING`, genuinely eliminates reasoning cost for models with native
Ollama thinking support, e.g. `qwen3.5:4b` — the model that produced the original bug
report) plus `options.num_predict`/`num_ctx` (`OLLAMA_NUM_PREDICT`/`OLLAMA_NUM_CTX`) as a
safety net for models that ignore the `think` field entirely (e.g. this repo's own local
default, `lfm2.5-thinking:latest`). Also raised the previously-hardcoded 300s HTTP timeout
to `OLLAMA_REQUEST_TIMEOUT` (default 600s), discovered necessary when the safety-net path
alone exceeded 300s in real testing. Went through Spec Kit specify/plan/tasks first
(`specs/005-fix-ollama-thinking-response/`) rather than being hot-patched from chat. See
`docs/SESSION_LOG.md`'s 2026-08-05 entry for the full record, including a `capture-brainstorm-note`
project skill added earlier the same session to capture the original bug report.

## Why
User hit the bug live while running `/skill generate_skill` against the local Ollama
backend, then explicitly asked that the fix go through spec-driven development rather
than being patched directly from the chat-based diagnosis that came with the bug report.

## Not being worked on right now (explicitly out of scope)
- `ISS-008` (full isolated-worker-with-RPC execution for skills/tools) — deferred,
  materially larger infrastructure item
- `ISS-005` (pre-existing, unrelated test failures) — logged, not fixed
- `ISS-006` (pyyaml root dependency hygiene) — logged, not fixed
- Swapping `OLLAMA_REMOTE_MODEL`/`OLLAMA_LOCAL_MODEL` away from thinking-capable models —
  discussed as a plausible complementary follow-up (a lighter, non-thinking, code-tuned
  model would likely be faster and avoid this whole class of issue for structured
  generation tasks) but explicitly a separate, deliberate decision, not bundled into this
  fix (the fix must be correct regardless of which model is configured).

## Milestone note
All three original critical audit findings (ISS-001/002/003) plus ISS-009 are now fixed.
Remaining open items are minor/pre-existing (`ISS-005`, `ISS-006`) or explicitly deferred
larger projects (`ISS-008`).
