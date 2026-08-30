# Quickstart: Skill Regeneration Diff

## Automated Validation

Run focused tests after implementation:

```powershell
uv run pytest tests/test_skill_diffing.py tests/test_generate_skill_regeneration.py -v
```

Run final validation:

```powershell
uv run pytest -q
uv run python -m compileall -q py_mono skills
```

## Manual Scenario

1. Start from an approved skill.
2. Regenerate that skill with changed behavior.
3. Confirm output shows lifecycle results and separate diffs for `SKILL.md` and `skill.py`.
4. Confirm the regenerated skill remains proposed until `/approve <skill>` is run.

## Missing Baseline Scenario

1. Attempt regeneration for a skill without an approved baseline.
2. Confirm output states that no approved baseline is available.
3. Confirm approval is still explicit.
