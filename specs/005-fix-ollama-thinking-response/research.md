# Phase 0 Research: Fix Ollama thinking-model empty response

No `[NEEDS CLARIFICATION]` markers remained in `spec.md`, but the spec's Assumptions section
flagged two things to verify against the actual running environment before committing to a
design: whether the local runtime honors a `think` request field, and whether raising the
response budget actually resolves the failure. Both were tested directly against real, running
Ollama servers during planning — not assumed from documentation or from the chat-based diagnosis
alone.

## Decision: `think: false` by default, with `options.num_predict`/`num_ctx` as a safety net

**Decision**: Send `"think": false` on every Ollama chat request by default
(`OLLAMA_ENABLE_THINKING=false`), *and* set an explicit `options.num_predict`/`num_ctx` on every
request regardless. `OLLAMA_ENABLE_THINKING=true` omits the `think` field (letting a model reason
natively) but keeps the budget safety net in place.

**Rationale — this took two rounds of empirical testing to get right, and the first round's
conclusion was wrong**: The original bug report (`docs/ISSUES.md` ISS-009,
`kb-template/knowledge/raw/brainstorm-20260805-ollama-thinking-empty-response.md`) came with a
diagnosis from claude.ai recommending `"think": false` as the primary fix.

*Round 1 — testing against the wrong model first led to rejecting `think: false`.* Tested
against this agent's **local default** model, `lfm2.5-thinking:latest`
(`http://localhost:11434`): `"think": false` did **not** stop it from reasoning — the full
`<think>...</think>` block still came through, just embedded inline in `content` instead of a
separate field. Token cost was unaffected. This looked like clear evidence to reject `think:
false` and rely purely on budget (`options.num_predict`/`num_ctx`), which reliably reproduced
the failure at a small budget (`num_predict: 15` → `content: ""`, `done_reason: "length"`,
non-empty separate `message.thinking` field) and — after a false start at `num_predict: 3072`
still truncating on a realistic prompt (see below) — resolved it at `num_predict: 4096` on the
real, realistic `generate_skill` prompt (`eval_count: 1893`, `done_reason: "stop"`, real content
returned).

*Round 2 — testing against the actual model from the bug report reversed that conclusion.* The
remote host referenced in `.env`/`OLLAMA_REMOTE_URL` (confirmed reachable during planning,
model `qwen3.5:4b` — the actual model that produced the original bug report) was tested
directly: `"think": false` against `qwen3.5:4b` produced `content: "PONG"`, **no `thinking`
field at all**, `eval_count: 3` (essentially zero reasoning tokens spent), `done_reason:
"stop"`. This is the opposite result from `lfm2.5-thinking:latest` — `qwen3.5:4b` has native
Ollama thinking support and genuinely honors `think: false`, eliminating the reasoning cost
entirely rather than just relocating it. Confirmed harmless/ignored (no error, no format change)
on a genuinely non-thinking model too (`granite4:350m`).

**Conclusion**: model behavior for `think` is not uniform — some models honor it fully, at least
one in active use here (`lfm2.5-thinking:latest`) ignores it. A single-lever fix would leave one
of the two models this agent actually uses unprotected. Sending `think: false` by default is
free/effective for the compliant model (the one that produced the original bug) and harmless for
the non-compliant one; the budget safety net protects the non-compliant one regardless.

**Final end-to-end confirmation**: the exact combination the implemented code now sends
(`think: false` + `options.num_predict: 4096` + `options.num_ctx: 8192`) was tested directly
against `lfm2.5-thinking:latest` with the realistic prompt — `done_reason: "stop"`,
`eval_count: 1764` (well under budget), content non-empty with a properly *closed* `<think>...
</think>` block (Shape A, see `contracts/ollama-chat-request-contract.md`) followed by the real
answer — confirming existing `_strip_thinking()` handling applies cleanly. Combined with the
`qwen3.5:4b` confirmation above, both models this agent actually uses were validated against the
literal final payload shape, not just individual levers in isolation.

**A second correction, also discovered mid-planning**: `qwen3.5:4b` reasons far more verbosely on
this class of prompt than the original bug report's `eval_count: 3645` suggested as an upper
bound — re-testing with `num_predict: 3072` (no `think` field) on a realistic prompt **still**
produced empty `content` with `done_reason: "length"`, `eval_count` exactly hitting the budget.
This is exactly why `think: false` matters as the primary lever rather than only raising the
budget further: for `qwen3.5:4b`, budget alone would require guessing an upper bound for an
apparently very verbose, self-questioning reasoning process (visible in the captured `thinking`
text — extensive, repetitive deliberation over minor formatting choices); `think: false` sidesteps
that uncertainty entirely by not reasoning at all for this model.

**Alternatives considered**:
- *`options.num_predict`/`num_ctx` alone, no `think` field* (Round 1's conclusion) — superseded.
  Works for `lfm2.5-thinking:latest` but leaves `qwen3.5:4b` dependent on guessing a budget large
  enough for an unpredictably verbose reasoning process, and burns significant time/tokens even
  when it does work (multiple minutes per call in testing).
- *Prompt simplification* (claude.ai's Fix 4) — rejected as a primary fix. Might reduce reasoning
  length for one specific prompt, but doesn't address the underlying problem, and isn't something
  `OllamaProvider` can enforce on every caller's prompt content (FR-004 — fix must live in the
  shared provider, not per-call-site prompt engineering).
- *Leaving `num_predict`/`num_ctx` unset and relying on server defaults* — rejected regardless of
  the `think` decision. The original failure happened with no explicit budget set at all,
  meaning whatever the server's effective default was, it was already too small. An explicit
  default removes the dependency on server/version-specific defaults this agent doesn't control.

## Decision: raise the HTTP request timeout to accommodate the safety-net path

**Decision**: Add `OLLAMA_REQUEST_TIMEOUT` (default `600` seconds), replacing the previously
hardcoded `timeout=300` in `requests.post()`.

**Rationale**: Discovered directly during planning, not anticipated in the original spec: testing
`OllamaProvider.generate()` (with the `num_predict=4096` safety net in place, before the `think:
false` fix was added) against `qwen3.5:4b` on the realistic prompt **raised
`requests.exceptions.ReadTimeout`** — the call took longer than the hardcoded 300s because this
model generates at roughly 9-10 tokens/second on the observed hardware, and 4096 tokens of pure
reasoning exceeds 300s. This would have turned the original "silent empty response" bug into a
new "unhandled exception" bug for any model/path that still relies on the budget safety net
(non-`think`-compliant models, or `OLLAMA_ENABLE_THINKING=true`). Raising the timeout is
necessary even though the default `think: false` path is fast in practice (~5s including cold
model load, confirmed in testing) — the timeout only matters for the slower fallback path, and
600s gives comfortable headroom over the observed ~436s worst case for a 4096-token budget at
this measured rate.

## Decision: Surface `message.thinking` in debug output, without using it as return text

**Decision**: When present, `message.thinking` is included in existing `DEBUG` log output
alongside `message.content`. It is never used as the returned response text — only `content` is
returned, unchanged from today's contract.

**Rationale**: Confirmed by testing (above) that this provider/model combination does return a
genuinely separate `thinking` field distinct from `content`. Logging it costs nothing and
directly satisfies FR-005 (a future empty-`content` failure should be diagnosable from existing
debug output without new instrumentation) — an operator can immediately see whether the model
was mid-reasoning when it got cut off, rather than only seeing an opaque empty string.

**Alternatives considered**:
- *Fall back to `thinking` as the response text when `content` is empty* — rejected. `thinking`
  is explicitly the model's internal reasoning, not a validated answer to the original prompt;
  treating it as the real output would violate FR-003 (must not silently manufacture output that
  wasn't actually the model's answer) and could produce structurally invalid output (e.g. not
  valid SKILL.md content) that looks superficially like a success.

## Decision: Configurable via `py_mono/config.py`, defaulting to fixed behavior

**Decision**: Add `OLLAMA_ENABLE_THINKING` (default `false`), `OLLAMA_NUM_PREDICT` (default
`4096`), `OLLAMA_NUM_CTX` (default `8192`), and `OLLAMA_REQUEST_TIMEOUT` (default `600`) to
`py_mono/config.py`, following the exact env-var-with-boolean/value-default pattern already used
for `ENABLE_SHELL_TOOL`/`ENABLE_DYNAMIC_TOOLS` and `OLLAMA_MODEL`/`OLLAMA_BASE_URL`.

**Rationale**: Matches existing configuration conventions (documented in the module docstring,
`os.getenv` with a sensible default) rather than inventing a new configuration mechanism. The
budget default is informed by direct testing: `num_predict: 3072` proved insufficient for
`qwen3.5:4b` on a realistic prompt when `think` isn't suppressed, while `num_predict: 4096`
resolved the equivalent case for `lfm2.5-thinking:latest` (`eval_count: 1893`, comfortable
margin). This default matters primarily as a safety net (see the `think: false` decision above)
— for the compliant model it's rarely exercised at all.

**Alternatives considered**:
- *Hard-code the budget values in `ollama_provider.py`* — rejected; every other Ollama-related
  tunable in this codebase is environment-configurable, and an operator with a more complex
  prompt or a slower/faster model may reasonably need to raise or lower this.
- *Per-model budget table* — rejected as unnecessary complexity (Principle I) for a first fix;
  a single generous default, uniformly applied, addresses the reported bug without needing to
  maintain a table of model-specific behaviors this codebase doesn't otherwise track.
