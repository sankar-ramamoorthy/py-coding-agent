# Next Actions

Ordered, concrete next steps. Check off and move to `SESSION_LOG.md` history when done,
don't just delete — `SESSION_LOG.md` keeps the record.

- [x] Fix skill/dynamic-tool approval gate (ISS-003, branch `fix-skill-tool-approval-gate`)
- [x] Verify end-to-end against the real running container
- [x] Update `docs/ISSUES.md` and the session-handoff docs at end of session
- [ ] Review the `fix-skill-tool-approval-gate` branch, then push and open a PR into `main`
- [ ] Decide next: all three original critical audit findings (C-01/C-02/C-03) are now
      resolved — pick from `ISS-005`, `ISS-006`, `ISS-008`, or something new
- [ ] (Later, separate work) `ISS-008`: full isolated-worker-with-RPC execution for
      skills/dynamic tools (materially larger infrastructure project)
- [ ] (Later, separate work) `ISS-005`: investigate the pre-existing `tests/test_listallpy_skill.py`
      collection error and the two failing `tests/tools/test_create_tool.py` assertions
- [ ] (Later, separate work) `ISS-006`: declare `pyyaml` explicitly in the root `pyproject.toml`
- [ ] (Later, separate work) Decide on splitting `kb-template/` into its own repo
- [ ] (Later, separate work) Consider migrating other internal knowledge-base projects onto the schema
