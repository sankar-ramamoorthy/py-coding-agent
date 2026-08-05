# Quickstart: Validate the pre-existing-test-failures fix

## Prerequisites

- Project venv with dev dependencies installed (`pytest`).
- Branch `fix-pre-existing-test-failures`.

## Scenario 1 — Full suite is green

```bash
python -m pytest -q
```

**Expected**: All tests pass or skip only for the pre-existing, unrelated, environment-specific
reason (`tests/utils/test_path_utils.py` symlink-privilege skip on native Windows). No
collection errors, no failures.

## Scenario 2 — `listallpy` reflects its mocked tool, not the real filesystem

```bash
python -m pytest tests/test_listallpy_skill.py -v
```

**Expected**: Both tests pass — the skill's output matches the JSON payload the test's mock
`list_files` tool returns, not the actual repository's `.py` files.

## Scenario 3 — Skill approval survives a simulated cross-platform checkout

```bash
python -m pytest tests/test_approval_ledger.py tests/test_skill_load_gating.py -v
```

**Expected**: All pass, including `test_all_real_approved_skills_still_load` (every currently
`approved` skill loads) and the new line-ending-equivalence tests.

## Scenario 4 — `create_tool` messages match its actual behavior

```bash
python -m pytest tests/tools/test_create_tool.py -v
```

**Expected**: All 5 tests pass, including the two that previously failed on stale message-text
and code-shape assumptions.

## Scenario 5 — No compile regressions

```bash
python -m compileall -q py_mono skills
```

**Expected**: Exits 0, no output.
