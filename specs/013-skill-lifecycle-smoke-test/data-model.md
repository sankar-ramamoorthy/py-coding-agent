# Data Model: Skill Lifecycle Smoke Test

## SkillLifecycleRun

Represents one attempt to take a skill request through the first M7 lifecycle slice.

**Fields**:
- `skill_name`: normalized skill identifier.
- `description`: user-provided skill description.
- `stages`: ordered collection of `LifecycleStageResult`.
- `final_status`: one of `failed`, `proposed`.
- `skill_path`: target skill directory when files are written.

**Validation rules**:
- Must preserve stage order: Critique, Generate, Validate, Test, Propose.
- Must not reach Propose if Validate or Test failed.
- Must not mark a skill approved.

## LifecycleStageResult

Represents the outcome of one lifecycle stage.

**Fields**:
- `stage`: one of `critique`, `generate`, `validate`, `test`, `propose`.
- `status`: one of `passed`, `failed`, `skipped`.
- `message`: short user-facing summary.
- `details`: optional failure reason or warning list.

**Validation rules**:
- Failed stages must include a useful failure reason.
- Skipped stages must identify the prior failed dependency.
- Stage names and statuses must be stable enough for tests to assert.

## SmokeTestResult

Represents the synthetic pre-approval run of generated skill code.

**Fields**:
- `status`: `passed` or `failed`.
- `request`: synthetic request string used for the run.
- `output_preview`: short preview of successful output, if any.
- `failure_reason`: exception or invalid-output reason, if failed.

**Validation rules**:
- A smoke-test failure blocks the Propose stage.
- The smoke run must not approve or ledger-record the generated skill.

## ProposedSkill

Represents the generated skill artifacts awaiting human approval.

**Fields**:
- `skill_name`
- `skill_md_content`
- `skill_py_content`
- `skill_path`
- `status`: always `proposed` for this feature.

**State transitions**:
- `generated` -> `validated` after static validation passes.
- `validated` -> `smoke_tested` after the smoke run passes.
- `smoke_tested` -> `proposed` after files are saved and review instructions are shown.
- Any validation or smoke-test failure -> `failed`, with no approval-ready presentation.
