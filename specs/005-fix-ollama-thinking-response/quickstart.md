# Quickstart: Validate the Ollama thinking-model fix

Validates that a thinking-capable Ollama model no longer returns an empty response by exhausting
its budget on internal reasoning, and that non-thinking-model / non-Ollama behavior is
unaffected.

## Prerequisites

- A running Ollama server reachable from the agent (local `http://localhost:11434` or the
  configured remote/GPU host).
- A thinking-capable model available on that server (e.g. `qwen3.5:4b`, `lfm2.5-thinking:latest`
  — both confirmed thinking-capable during planning; see `research.md`).
- This feature's implementation landed in `py_mono/llm/ollama_provider.py` and
  `py_mono/config.py` (see `plan.md` Technical Context / `tasks.md`).

## Scenario 1 — Reproduce the original failure (pre-fix baseline)

Direct API call, bypassing the provider, with a deliberately constrained budget — this is what
the unfixed provider effectively did (no budget set → server's own too-small effective default):

```bash
curl -s http://<ollama-host>:11434/api/chat -d '{
  "model": "<thinking-capable model>",
  "messages": [{"role": "user", "content": "<a moderately complex structured-generation prompt>"}],
  "stream": false,
  "options": {"num_predict": 200}
}'
```

**Expected (pre-fix baseline)**: `message.content` is `""`, `message.thinking` is non-empty,
`done_reason` is `"length"`. This exact shape was reproduced during planning against both
`lfm2.5-thinking:latest` (local) and `qwen3.5:4b` (remote, the model from the original bug
report) — see `research.md`.

## Scenario 2 — Confirm the fix via the real provider

```bash
docker compose run --rm py-coding-agent
```

Inside the running agent, with `OLLAMA_MODEL`/`LLM_PROVIDER` pointed at a thinking-capable model:

```text
> /skill generate_skill listrecentfiles | list all files in current directory created in the last hour
```

**Expected (post-fix)**: The call completes and returns generated `SKILL.md` content (or a
validation-warning response), not `❌ LLM call failed while generating SKILL.md. Try again.`

## Scenario 3 — No regression for non-thinking models

Repeat Scenario 2 with `OLLAMA_MODEL` set to a non-thinking model (e.g. `granite4:350m`,
`qwen2.5-coder:latest`).

**Expected**: Behavior identical to before this fix — non-thinking models were never affected by
the bug and must not be affected by the fix either (FR-002).

## Scenario 4 — Debug visibility

With `DEBUG = True` in `py_mono/llm/ollama_provider.py` (default), trigger a call to a
thinking-capable model with a tight `OLLAMA_NUM_PREDICT` (e.g. temporarily set to `100` to force
truncation on a complex prompt).

**Expected**: The printed debug output includes the `thinking` field's content alongside
`content`, making it possible to tell from the logs alone that the model was cut off mid-reasoning
(FR-005) — without needing to add new print statements to investigate.

## Automated verification

```bash
pytest tests/llm/test_ollama_provider.py -v
```

**Expected**: All existing tests pass unchanged, plus new tests added for this feature (payload
includes `options.num_predict`/`num_ctx`; `thinking` field is logged when present; empty-content
failure path still triggers for non-truncation causes). See `tasks.md` for the specific test
cases.
