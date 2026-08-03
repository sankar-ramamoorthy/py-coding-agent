# Next Actions

Ordered, concrete next steps. Check off and move to `SESSION_LOG.md` history when done,
don't just delete — `SESSION_LOG.md` keeps the record.

- [x] Add dual Ollama backend selection (ISS-007, branch `ollama-dual-backend`)
- [x] Verify end-to-end against real backends (mocked tests + live remote/local/fallback/
      model-switch/backward-compat checks)
- [x] Update `docs/ISSUES.md` and the session-handoff docs at end of session
- [ ] Review the `ollama-dual-backend` branch, then push and open a PR into `main`
- [ ] Decide next: ISS-002/ISS-003 (the original C-02/C-03 security findings), or something else
- [ ] (Later, separate work) ISS-005: investigate the pre-existing `tests/test_listallpy_skill.py`
      collection error and the two failing `tests/tools/test_create_tool.py` assertions
- [ ] (Later, separate work) ISS-006: declare `pyyaml` explicitly in the root `pyproject.toml`
- [ ] (Later, separate work) Decide on splitting `kb-template/` into its own repo
- [ ] (Later, separate work) Consider migrating TradeForge-KnowledgeBase / AITrader onto the schema
- [ ] (Later, separate work) ISS-002: sandbox path-check bypass remediation
- [ ] (Later, separate work) ISS-003: pre-approval arbitrary code execution remediation
