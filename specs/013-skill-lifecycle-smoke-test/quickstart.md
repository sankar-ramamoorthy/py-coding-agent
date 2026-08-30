# Quickstart: Skill Lifecycle Smoke Test

## Prerequisites

- Dependencies are installed via the existing `uv` workflow.
- The working tree is on an implementation branch for `ISS-015`.

## Automated Validation

Run the focused tests for this feature:

```powershell
uv run pytest tests/test_skill_lifecycle.py tests/test_generate_skill.py -v
```

Run the broader safety checks before merge:

```powershell
uv run pytest -q
uv run python -m compileall -q py_mono skills
```

## Manual CLI Scenario

Start the agent through the existing Docker-first workflow:

```powershell
docker compose run --rm py-coding-agent
```

Generate a simple skill:

```text
/skill generate_skill echo-request | Return the request text unchanged.
```

Expected outcome:

- The response lists Critique, Generate, Validate, Test, and Propose in order.
- Validate and Test pass for the simple generated skill.
- The final status remains proposed, not executable.
- The response still tells the user to review, approve, then run the skill.

Attempt to run before approval:

```text
/skill echo-request hello
```

Expected outcome:

- The existing approval gate blocks normal execution until approval.

## Failure Scenario

Use a test stub or controlled generated implementation that passes static validation but raises
during `run()`.

Expected outcome:

- The lifecycle reports Test as failed.
- Propose does not pass.
- The skill is not presented as approval-ready.
