# Implementation Plan: Skill Lifecycle Smoke Test

**Branch**: `013-skill-lifecycle-smoke-test` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/013-skill-lifecycle-smoke-test/spec.md`

## Summary

Add the first M7 lifecycle slice to skill generation: produce stage results for Critique,
Generate, Validate, Test, and Propose; run a synthetic smoke check after static validation; and
surface a clear pre-approval report while preserving the existing proposed/approved trust
boundary. The implementation should extend `generate_skill` with a small reusable lifecycle
result model and smoke-test helper rather than changing the approval ledger or normal skill
execution path.

## Technical Context

**Language/Version**: Python >=3.10

**Primary Dependencies**: Existing project dependencies only; no new runtime dependency.

**Storage**: Existing skill files under `skills/<skill_name>/`; existing telemetry
`telemetry/skill_runs.jsonl` for any actual skill execution records; no new persistent store.

**Testing**: `pytest`; add focused unit tests for lifecycle result/smoke-test behavior and
integration-style tests for `skills/generate_skill/skill.py` using stubs.

**Target Platform**: Docker-first Python CLI workflow, with direct local execution still
supported.

**Project Type**: Single Python project with repo-level skill packages.

**Performance Goals**: Add only one synthetic run after validation; successful generation should
not require more than one additional lifecycle step beyond the current flow.

**Constraints**: Do not auto-approve, auto-load, or bypass the existing approval ledger. Do not
change provider/session logic. Do not add isolated-worker execution in this slice.

**Scale/Scope**: Small M7 slice touching skill-generation behavior only: one new helper module
or equivalent focused helper, `skills/generate_skill/skill.py`, and tests.

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS -- feature is scoped to the existing
  skill-generation path and a small helper; no directory restructuring or framework changes.
- **Principle II (Provider-Agnostic Core)**: PASS -- no provider-specific routing or model logic
  is added.
- **Principle III (Tool, Skill, and Playbook Separation)**: PASS -- smoke execution must use the
  normal skill interface and approved helper boundaries, not direct tool function calls.
- **Principle IV (Test Coverage for New Behavior)**: PASS -- tasks include new tests for
  lifecycle stage reporting, validation failure, smoke-test failure, and approval boundary.
- **Principle V (Incremental Change Philosophy)**: PASS -- diff-on-regeneration,
  failure-driven evolution, package signing, and isolated workers stay out of scope.

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/013-skill-lifecycle-smoke-test/
|-- spec.md
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- skill-lifecycle-output.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
py_mono/skill/lifecycle.py           # new: lifecycle stage result and smoke-test helpers
skills/generate_skill/skill.py       # extend generation flow to report lifecycle stages
tests/test_skill_lifecycle.py        # new: helper and smoke-test behavior
tests/test_generate_skill.py         # new: generate_skill integration behavior with stubs
```

**Structure Decision**: Put shared lifecycle mechanics under `py_mono/skill/` alongside
validation, approval, telemetry, and fitness. Keep `generate_skill` responsible for orchestration
and user-facing output.

## Complexity Tracking

No constitution violations or extra complexity exceptions.
