# Contract: Skill Review Command

## Command

```text
/skill review <skill-name>
```

## Successful Review Output

The output includes:

- `Review: <skill-name>`
- `Status: <report-status>`
- `Mode: <create|regenerate|evolve>`
- `Candidate: <path>` when present
- `Lifecycle report: <path>` when present
- Stage summary lines
- Smoke-test summary when present
- Diff summary lines when present
- Next steps including `/approve <skill-name>`

## Missing Report Output

If no lifecycle report is available, the output explains the missing report and shows whether a candidate directory exists.

## Existing Command Changes

- `/skill list` marks pending candidates and shows `/skill review <name>`.
- `/skill help <name>` shows the SKILL.md content and a pending-candidate notice when applicable.
- `/approve <name>` states whether a candidate was promoted and gives the retained report path when available.
