# Quickstart: Isolated Worker Execution

## Validation Commands

Run focused tests:

```bash
uv run pytest -q tests/test_skill_worker.py tests/test_skill_load_gating.py tests/tools/test_tool_loader.py
```

Run the full baseline:

```bash
uv run pytest -q
uv run python -m compileall -q py_mono skills
```

## Manual Scenario

1. Start the agent.
2. Run an approved skill that calls an allowed tool.
3. Confirm the skill result returns normally.
4. Create a dynamic tool, enable dynamic tools, reload tools, and run it.

Expected result: generated extension modules are not imported in the main agent process during discovery and execute only through worker subprocesses.
