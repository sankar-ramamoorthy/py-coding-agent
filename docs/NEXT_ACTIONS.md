# Next Actions

Ordered, concrete next steps. Check off and move to `SESSION_LOG.md` history when done,
don't just delete — `SESSION_LOG.md` keeps the record.

- [x] Fix skill/dynamic-tool approval gate (ISS-003) — merged, PR #82
- [x] Fix README/kb-template documentation drift — merged, PR #83
- [x] Add py-coding-agent lifecycle one-pager; redact cross-project references — merged, PR #84
- [x] Add `capture-brainstorm-note` skill; file and spec ISS-009 — merged, PR #85
- [x] Fix Ollama thinking-model empty response (ISS-009, branch `fix-ollama-thinking-response`)
- [x] Verify end-to-end against real Ollama servers (both models this agent uses)
- [x] Update `docs/ISSUES.md` and the session-handoff docs at end of session
- [ ] Review the `fix-ollama-thinking-response` branch, then push and open a PR into `main`
- [ ] Decide next: pick from `ISS-005`, `ISS-006`, `ISS-008`, the model-swap follow-up
      noted in `docs/CURRENT_FOCUS.md`, or something new
- [ ] (Later, separate work) `ISS-008`: full isolated-worker-with-RPC execution for
      skills/dynamic tools (materially larger infrastructure project)
- [ ] (Later, separate work) `ISS-005`: investigate the pre-existing `tests/test_listallpy_skill.py`
      collection error and the two failing `tests/tools/test_create_tool.py` assertions
- [ ] (Later, separate work) `ISS-006`: declare `pyyaml` explicitly in the root `pyproject.toml`
- [ ] (Later, separate work) Decide on splitting `kb-template/` into its own repo
- [ ] (Later, separate work) Consider migrating other internal knowledge-base projects onto the schema
- [ ] (Later, separate work) Consider swapping `OLLAMA_REMOTE_MODEL`/`OLLAMA_LOCAL_MODEL` to a
      lighter, non-thinking, code-tuned model (e.g. a quantized Qwen2.5-Coder 7B) for structured
      generation tasks — discussed 2026-08-05, not decided
