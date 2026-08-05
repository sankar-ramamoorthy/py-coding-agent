# Next Actions

Ordered, concrete next steps. Check off and move to `SESSION_LOG.md` history when done,
don't just delete — `SESSION_LOG.md` keeps the record.

- [x] Fix skill/dynamic-tool approval gate (ISS-003) — merged, PR #82
- [x] Fix README/kb-template documentation drift — merged, PR #83
- [x] Add py-coding-agent lifecycle one-pager; redact cross-project references — merged, PR #84
- [x] Add `capture-brainstorm-note` skill; file and spec ISS-009 — merged, PR #85
- [x] Fix Ollama thinking-model empty response (ISS-009) — merged, PR #86
- [x] Verify end-to-end against real Ollama servers (both models this agent uses)
- [x] File ISS-010 (bare `/provider` falls through to the LLM instead of showing usage) —
      to be fixed later via Spec Kit, not fixed this session
- [ ] Decide next: pick from `ISS-005`, `ISS-006`, `ISS-008`, `ISS-010`, the model-swap
      follow-up noted in `docs/CURRENT_FOCUS.md`, or something new
- [ ] (Later, separate work) `ISS-010`: bare `/provider` (no argument) in
      `py_mono/agent/agent.py` should show a `Usage: /provider <provider> [model]` message
      instead of silently falling through to the LLM — route through Spec Kit
- [ ] (Later, separate work) `ISS-008`: full isolated-worker-with-RPC execution for
      skills/dynamic tools (materially larger infrastructure project)
- [ ] (Later, separate work) `ISS-005`: investigate the pre-existing `tests/test_listallpy_skill.py`
      collection error and the two failing `tests/tools/test_create_tool.py` assertions
- [ ] (Later, separate work) `ISS-006`: declare `pyyaml` explicitly in the root `pyproject.toml`
- [ ] (Later, separate work) Decide on splitting `kb-template/` into its own repo
- [ ] (Later, separate work) Consider migrating other internal knowledge-base projects onto the schema
- [ ] (Later, separate work) Consider swapping `OLLAMA_REMOTE_MODEL`/`OLLAMA_LOCAL_MODEL` to a
      lighter, non-thinking, code-tuned model (e.g. a quantized Qwen2.5-Coder 7B) for structured
      generation tasks — discussed 2026-08-05, not decided; user has begun testing
      `qwen2.5-coder:7b-instruct-q5_K_M` via `/provider ollama-auto <model>`
