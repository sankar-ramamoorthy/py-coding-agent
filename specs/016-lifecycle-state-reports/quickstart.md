# Quickstart: Lifecycle State Reports

## Validation Commands

Run focused tests:

```bash
uv run pytest -q tests/test_skill_lifecycle_reporting.py tests/test_generate_skill.py
```

Run the full baseline:

```bash
uv run pytest -q
uv run python -m compileall -q py_mono skills
```

## Manual Scenario

1. Start the agent.
2. Generate a new skill:

   ```text
   /skill generate_skill echo-request | Return the request text unchanged.
   ```

3. Inspect `skills/echo-request/lifecycle_report.md`.
4. Regenerate or evolve an existing skill.
5. Inspect `skills/<skill-name>/.candidate/lifecycle_report.md`.

Expected result: reports include lifecycle stage outcomes, smoke-test details, candidate path, next approval command, and diffs for regeneration/evolution.
