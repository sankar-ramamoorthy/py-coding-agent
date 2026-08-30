# Contract: Skill Regeneration Diff Output

## Successful Diff Output

Regeneration output must include:

- Skill name.
- Lifecycle result from `ISS-015`.
- Baseline status: available, unavailable, or unchanged.
- Separate diff sections for `SKILL.md` and `skill.py` when a baseline is available.
- Proposed status and explicit approval next step.

## Missing Baseline Output

When no approved baseline is available, output must include:

- Skill name.
- Explanation that diff evidence is unavailable.
- Reason if known.
- Proposed status only if the regenerated candidate passed the lifecycle.
- Explicit approval requirement.

## Safety Boundary

The diff output must never imply that review evidence approved the skill.
