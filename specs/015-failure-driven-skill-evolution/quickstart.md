# Quickstart: Failure-Driven Skill Evolution

## Automated Validation

Run focused tests after implementation:

```powershell
uv run pytest tests/test_skill_evolution.py tests/test_generate_skill_evolution.py -v
```

Run final validation:

```powershell
uv run pytest -q
uv run python -m compileall -q py_mono skills
```

## Manual Scenario

1. Run an approved skill in a way that produces a recorded failure.
2. Request a failure-driven revision proposal for that skill.
3. Confirm the output summarizes the failure context.
4. Confirm the proposed revision runs through the `ISS-015` lifecycle.
5. Confirm the revised skill remains proposed until explicitly approved.

## Missing Context Scenario

1. Request failure-driven evolution for a skill with no usable failure context.
2. Confirm the system explains that no actionable failure context is available.
3. Confirm no regenerated proposal is created.
