# Next Actions

Ordered, concrete next steps. Check off and move to `SESSION_LOG.md` history when done,
don't just delete — `SESSION_LOG.md` keeps the record.

- [x] Fix workspace sandbox escape (ISS-002, branch `fix-workspace-sandbox`)
- [x] Verify end-to-end against the real running container
- [x] Update `docs/ISSUES.md` and the session-handoff docs at end of session
- [ ] Review the `fix-workspace-sandbox` branch, then push and open a PR into `main`
- [ ] Decide next: ISS-003 (skills/dynamic tools executing before approval, the last
      original critical audit finding), or something else
- [ ] (Later, separate work) ISS-005: investigate the pre-existing `tests/test_listallpy_skill.py`
      collection error and the two failing `tests/tools/test_create_tool.py` assertions
- [ ] (Later, separate work) ISS-006: declare `pyyaml` explicitly in the root `pyproject.toml`
- [ ] (Later, separate work) Decide on splitting `kb-template/` into its own repo
- [ ] (Later, separate work) Consider migrating TradeForge-KnowledgeBase / AITrader onto the schema
- [ ] (Later, separate work) True OS-level shell content sandboxing, if ever pursued
