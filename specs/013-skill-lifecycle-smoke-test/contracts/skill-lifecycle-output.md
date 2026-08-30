# Contract: Skill Lifecycle Output

## Scope

This contract describes the user-visible result from skill generation after `ISS-015`.

## Successful Lifecycle Result

When generation succeeds, the result must include:

- Skill name.
- Final status: proposed, not executable.
- Location of generated files.
- Ordered lifecycle stages:
  - Critique: passed or passed with warnings.
  - Generate: passed.
  - Validate: passed.
  - Test: passed, with a short smoke-run output preview when available.
  - Propose: passed.
- Existing next steps:
  - Review the generated skill.
  - Approve the skill explicitly.
  - Run the approved skill.

## Failed Lifecycle Result

When a stage fails, the result must include:

- Skill name.
- Failed stage name.
- Failure reason.
- Any later stages marked as skipped or omitted in a way that makes clear they did not run.
- A retry-oriented next step, without presenting the skill as approval-ready.

## Safety Boundary

Passing this lifecycle contract must never:

- Mark `SKILL.md` as approved.
- Write or update an approval ledger entry.
- Load the generated skill into the normal registry as executable.
- Call underlying tool functions directly.
