# Data Model: Lifecycle State Reports

## LifecycleReport

- `skill_name`: Canonical skill name for the lifecycle attempt.
- `mode`: One of `create`, `regenerate`, or `evolve`.
- `status`: Final report status, such as `proposed`, `failed`, or `report_failed`.
- `timestamp`: UTC timestamp when the report was written.
- `candidate_path`: Path containing proposed artifacts, if available.
- `skill_path`: Skill directory path.
- `stages`: Ordered lifecycle stage results.
- `smoke_test`: Smoke-test request, status, output preview, and failure reason when available.
- `diffs`: Diff records for regenerated or evolved artifacts.
- `baseline`: Approved baseline availability and reason when applicable.
- `failure_context`: Failure context for evolution proposals when available.
- `next_steps`: Human-readable review and approval guidance.

## LifecycleStage

- `stage`: Stage name.
- `status`: `passed`, `failed`, or `skipped`.
- `message`: Human-readable result.
- `details`: Optional detail lines.

## DiffRecord

- `artifact`: Artifact name, normally `SKILL.md` or `skill.py`.
- `changed`: Whether the artifact changed.
- `baseline_available`: Whether an approved baseline was available.
- `diff_text`: Rendered diff or baseline-unavailable reason.

## SmokeTestRecord

- `status`: Smoke-test status.
- `request`: Synthetic request used for the smoke test.
- `output_preview`: Preview of output when passed.
- `failure_reason`: Failure reason when failed.

## FailureContextRecord

- `request`: Original failed request.
- `failure_reason`: Captured failure.
- `provider`: Provider active during failure.
- `model`: Model active during failure.
- `timestamp`: Telemetry timestamp.
