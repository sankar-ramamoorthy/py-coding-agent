# Quickstart: Lifecycle CLI Review Polish

## Validation Commands

Run focused tests:

```bash
uv run pytest -q tests/test_special_commands.py tests/test_generate_skill.py
```

Run the full baseline:

```bash
uv run pytest -q
uv run python -m compileall -q py_mono skills
```

## Manual Scenario

1. Generate or regenerate a skill candidate.
2. Run:

   ```text
   /skill review <skill-name>
   ```

3. Confirm the output shows lifecycle status, candidate path, report path, smoke-test result, diff summary, and approval command.
4. Run:

   ```text
   /skill list
   /skill help <skill-name>
   /approve <skill-name>
   ```

Expected result: list/help point to review, and approval output states whether a candidate was promoted.
