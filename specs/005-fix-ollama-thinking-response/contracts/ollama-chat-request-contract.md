# Contract: `OllamaProvider.generate()` request/response handling

`OllamaProvider.generate()` is this agent's only integration point with Ollama's `/api/chat`
endpoint. This contract documents the request shape it must send and the response shape it must
handle after this fix, based on empirical testing against real Ollama servers (see
`research.md`) rather than documentation alone.

## Request (unchanged shape, new fields)

```json
{
  "model": "<configured model>",
  "messages": [ ... ],
  "stream": false,
  "think": false,
  "options": {
    "num_predict": "<configurable, default 4096>",
    "num_ctx": "<configurable, default 8192>"
  }
}
```

- `tools`, when present, is added exactly as today — this fix does not change tool-call
  handling.
- `options.num_predict`/`num_ctx` are new and MUST be present on every request regardless of the
  `think` setting below — safety net for models that don't honor `think` at all (empirically
  confirmed: `lfm2.5-thinking:latest` reasons regardless of this field).
- `think: false` MUST be present by default (`OLLAMA_ENABLE_THINKING=false`, the default).
  Empirically confirmed (see `research.md`) to genuinely eliminate reasoning and its token cost
  for models with native Ollama thinking support (`qwen3.5:4b` — the model that produced the
  original bug report), and confirmed harmless/ignored on non-thinking models
  (`granite4:350m`). When `OLLAMA_ENABLE_THINKING=true`, the `think` field is omitted entirely
  (not set to `true` — omission is how a model reasons natively) and the `options` safety net is
  what protects against truncation in that mode.

## Response — two content shapes a thinking-capable model may return

Confirmed by direct testing against the local default model and the configured remote model:

**Shape A — inline reasoning, single field** (observed from `lfm2.5-thinking:latest`
specifically when `think: false` is sent — this model doesn't honor the field to suppress
reasoning, but its presence changes where the reasoning text lands):
```json
{"message": {"role": "assistant", "content": "<think>...reasoning...</think>\n\nANSWER"}}
```
Already handled by existing per-skill `_strip_thinking()` regex stripping when reasoning
completes and the `</think>` tag closes. If truncated mid-reasoning under this shape, `content`
holds an *unclosed* `<think>` fragment rather than being empty — `_strip_thinking()`'s regex
requires a closing tag and won't match it, so this is a materially different (and less obviously
detectable) failure signature than Shape B below. The `options.num_predict`/`num_ctx` safety net
matters most for exactly this shape, since there's no clean empty-`content` signal to catch.

**Shape B — separate `thinking` field, empty `content`** (observed from `qwen3.5:4b` and from
`lfm2.5-thinking:latest` when no `think` field is sent at all; the shape directly implicated in
the original bug report):
```json
{"message": {"role": "assistant", "content": "ANSWER", "thinking": "...reasoning..."}}
```
When truncated mid-reasoning (`done_reason: "length"` before the budget covers reasoning +
answer), `content` is empty and `thinking` holds whatever reasoning was generated before the
cutoff — a clean, detectable signal.

## Provider MUST

- Send `options.num_predict`/`num_ctx` on every chat request (values configurable via
  `py_mono/config.py`, see `research.md` for chosen defaults).
- Continue reading `message.get("content", "")` as the primary text result — unchanged from
  today.
- Additionally read `message.get("thinking")` (may be absent or `None` for non-thinking models
  — must not error if missing) and include it in existing `DEBUG` log output when present, so a
  future empty-`content` failure is diagnosable from logs without new instrumentation (FR-005).
- Leave the existing empty-response failure path (`_call_llm` returning `None` on empty/blank
  text) intact for genuine failures unrelated to reasoning-budget exhaustion (FR-003).

## Provider MUST NOT

- Depend on a `think` field to control model behavior (not confirmed reliable).
- Change behavior for non-Ollama providers (LiteLLM/Groq/OpenAI/Anthropic) — out of scope.
- Silently drop or ignore a truncation event — it must still be visible in debug output even
  though this fix reduces how often it occurs.
