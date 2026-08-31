# Contract: Lifecycle Report Artifacts

Every lifecycle attempt that reaches a known skill name writes report files when the filesystem permits it.

## Paths

- New skill proposal: `skills/<skill-name>/lifecycle_report.md` and `skills/<skill-name>/lifecycle_report.json`
- Regeneration/evolution proposal: `skills/<skill-name>/.candidate/lifecycle_report.md` and `skills/<skill-name>/.candidate/lifecycle_report.json`
- Failed attempt before a candidate is saved: `skills/<skill-name>/lifecycle_report.md` and `skills/<skill-name>/lifecycle_report.json`

## Markdown Report Requirements

The Markdown report includes:

- Title naming the skill.
- Status, mode, timestamp, skill path, and candidate path when available.
- Ordered lifecycle stage table or list.
- Smoke-test request and result when a smoke test ran.
- Failure context when evolution used telemetry.
- Baseline and diff records for regeneration/evolution.
- Next steps for review or retry.

## JSON Report Requirements

The JSON report is an object with these keys:

- `skill_name`
- `mode`
- `status`
- `timestamp`
- `skill_path`
- `candidate_path`
- `stages`
- `smoke_test`
- `baseline`
- `diffs`
- `failure_context`
- `next_steps`

Unknown or unavailable optional sections use empty strings, empty arrays, or `null` rather than omitting the top-level key.
