# Contract: Failure-Driven Evolution Output

## Proposal Output

When failure-driven proposal succeeds, output must include:

- Skill name.
- Failure context summary.
- Lifecycle result from `ISS-015`.
- Proposed status.
- Explicit review and approval next steps.

## Unavailable Context Output

When no usable failure context exists, output must include:

- Skill name if known.
- Explanation that no actionable failure context is available.
- Suggested next action to reproduce or capture a failure.

## Safety Boundary

Failure-driven evolution output must never:

- Mark the revised skill approved.
- Write an approval ledger entry.
- Load the revised skill for normal execution.
- Replace approved behavior without explicit user approval.
