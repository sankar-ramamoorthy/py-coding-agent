# Research: Skill Lifecycle Smoke Test

## Decision: Keep the first M7 slice inside `generate_skill`

**Rationale**: The current product path for creating skills is
`/skill generate_skill <skill-name> | <description>`. Adding lifecycle stage reporting there
delivers value immediately without introducing a new command or changing CLI dispatch.

**Alternatives considered**:
- New top-level lifecycle command: rejected for the first slice because it would duplicate the
  existing creation path before proving the lifecycle behavior.
- Approval-path changes: rejected because M7 should not weaken or redefine the hash-ledger gate.

## Decision: Add a small lifecycle helper under `py_mono/skill/`

**Rationale**: Stage result formatting, pass/fail state, and smoke-test execution are reusable
concepts, but they are still skill-framework concerns. `py_mono/skill/` already owns validation,
approval, telemetry, and fitness behavior.

**Alternatives considered**:
- Inline everything in `skills/generate_skill/skill.py`: simpler initially, but likely to make
  later M7 slices harder to reason about.
- Put lifecycle code in `py_mono/agent/`: rejected because this is skill creation behavior, not
  provider-agnostic agent loop behavior.

## Decision: Smoke-test only after static validation succeeds

**Rationale**: `validate_skill_py` is the current safety screen for generated code. Running code
that already failed static validation would add risk and produce noisy failures.

**Alternatives considered**:
- Smoke-test every generated output: rejected because invalid code should stop at validation.
- Delay smoke testing until after approval: rejected because the point of M7's first slice is to
  give the human reviewer more evidence before approval.

## Decision: Smoke-test through a constrained temporary skill instance

**Rationale**: The generated skill should be instantiated and called once with a synthetic request
and the current skill context so obvious runtime failures surface. The result must not update the
approval ledger or make the skill normally runnable.

**Alternatives considered**:
- Use `run_skill_safe`: rejected for proposed generated output because it correctly blocks
  unapproved skills; the smoke run is a pre-approval check and must stay isolated from normal
  execution.
- Import generated code through `SkillRegistry`: rejected because the registry load path is tied
  to approved, ledger-matched skills.

## Decision: Reuse existing telemetry only where execution is already recorded

**Rationale**: M6 created `telemetry/skill_runs.jsonl` for skill execution. The first M7 slice
does not need a second durable log. If the implementation records smoke-run execution, it should
use the existing telemetry shape and remain best-effort.

**Alternatives considered**:
- New lifecycle log: rejected as extra storage and premature for this slice.
- No visibility beyond the response: acceptable for MVP, but the plan leaves room to reuse the
  existing telemetry stream if the implementation already has the provider/model context.
