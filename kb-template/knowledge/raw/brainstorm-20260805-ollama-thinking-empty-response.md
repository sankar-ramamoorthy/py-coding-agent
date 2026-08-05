---
title: Ollama thinking-model empty response in generate_skill
type: raw-note
status: draft
project: py-coding-agent
authority: tool-specific-guidance
created: 2026-08-05
updated: 2026-08-05
canonical: false
related: []
---

# Ollama thinking-model empty response in generate_skill

## Trigger

Running `/skill generate_skill listrecentfiles | list all files in current directory created in
the last hour` against local Ollama (`qwen3.5:4b`) to scaffold a new skill.

## Raw Input

Debug payload sent to Ollama:

```
[DEBUG] Sending to Ollama:
{
  "model": "qwen3.5:4b",
  "messages": [
    {
      "role": "user",
      "content": "You are generating a SKILL.md file for a Python coding agent skill. Output ONLY the raw SKILL.md content. Do NOT include markdown code fences. Do NOT include any explanation or preamble. Skill name: listrecentfiles ... [full generate_skill SKILL.md-generation prompt, with allowed tools list and required output format/rules]"
    }
  ],
  "stream": false
}
```

Response (truncated):

```
{
  "done": true,
  "done_reason": "length",
  "total_duration": 62447003703,
  "load_duration": 341362175,
  "prompt_eval_count": 451,
  "prompt_eval_duration": 1006992000,
  "eval_count": 3645,
  "eval_duration": 60980906000
}
LLM returned empty response
❌ LLM call failed while generating SKILL.md. Try again.
```

claude.ai's diagnosis and 4 suggested fixes:

- **Diagnosis:** classic Ollama "thinking model" issue. `eval_count` 3645 tokens generated but
  `done_reason: "length"` — hit the token cap. Empty response strongly suggests qwen3.5 spent
  essentially all 3645 tokens in its internal `<think>...</think>` reasoning block and never got
  to emit the actual SKILL.md content before being cut off. Known behavior with Qwen3/3.5
  hybrid-thinking models served through Ollama.
- **Fix 1 (most likely effective):** disable thinking mode for this call via a `"think": false`
  field in the Ollama request payload.
- **Fix 2:** if keeping thinking on, raise the token budget substantially via
  `options.num_predict` (e.g. 4096) and make sure `options.num_ctx` is large enough (e.g. 8192)
  to hold it.
- **Fix 3:** check how the response is being parsed — if `think:false` isn't respected, the
  response may come back as `{"message": {"content": "", "thinking": "<the 3645 tokens>"}}`,
  i.e. reasoning and content are separate fields, and only `content` is being read. Worth
  logging the full `message` object once to confirm.
- **Fix 4:** simplify the prompt — long, highly-structured instructions can push a small
  reasoning model into over-thinking; consider stripping the Rules section down or using a
  `/no_think` shorthand if the Ollama/Qwen build supports it.
- Recommended trying Fix 1 first since it directly targets the symptom (huge reasoning token
  count, zero output).

## Observations

Grounded by reading the actual code (`py_mono/llm/ollama_provider.py` and
`skills/generate_skill/skill.py`), not just the pasted log:

- `OllamaProvider.generate()` (`py_mono/llm/ollama_provider.py`, payload built ~line 90-96)
  sends only `{"model", "messages", "stream"}` — no `"think"` field, no `"options"` dict with
  `num_predict`/`num_ctx` at all. Every thinking-capable Ollama model gets zero guidance from
  this provider, not just this one call.
- This is a **shared-provider code path** — every skill and every agent LLM call routed through
  Ollama goes through this same `generate()` method — so the bug is not specific to
  `generate_skill`; it would reproduce for any skill or any call using a thinking-capable Ollama
  model.
- `generate_skill` itself is already documented as **deprecated** in this repo's own
  `docs/skills.md` and `README_Skills.md`, in favor of `create_skill_py` — relevant to deciding
  where a fix should land.
- In `skills/generate_skill/skill.py`'s `_call_llm()` method, the empty-string check
  (`if not text or not text.strip(): logger.error(...); return None`) runs *before*
  `_strip_thinking()` is ever called — so the existing `<think>` tag-stripping logic never gets
  a chance to run when the provider returns truly empty content. Not the root cause, but worth
  recording so nobody assumes stripping already handles this case.

## Ideas

- claude.ai's 4 fixes above (`think: false`; raise `num_predict`/`num_ctx`; check for a separate
  `thinking` response field; simplify the prompt).
- Fix this at the `OllamaProvider` level, not per-skill, so every caller benefits.
- Add explicit test coverage for thinking-model handling rather than leaving it implicit.

## Questions

- Does the local Ollama server/model build actually honor a `think` request param, or does it
  need `options.num_predict`/`num_ctx` instead (behavior can vary by Ollama version and model
  template)?
- Should thinking be disabled unconditionally for all Ollama calls in this agent, or made
  configurable per-model?

## Concerns

- A provider-level change affects every skill and every Ollama-backed call in the agent; needs
  test coverage before landing, not a silent tweak.

## Possible Next Outputs

- Issue candidate — add to `docs/ISSUES.md`.
- Spec Kit spec candidate — the actual fix should go through `/speckit-specify` →
  `/speckit-plan` → ... rather than being hot-patched from this note.
- ~~No action~~ — not applicable; this is a live bug.
