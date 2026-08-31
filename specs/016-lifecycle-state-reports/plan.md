# Implementation Plan: Lifecycle State Reports

**Branch**: `iss-018-lifecycle-reports` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/016-lifecycle-state-reports/spec.md`

## Summary

Add lightweight durable lifecycle reports for generated, regenerated, and evolved skill candidates. The implementation will reuse the existing lifecycle, diffing, smoke-test, and evolution data structures, then persist a Markdown report plus JSON sidecar next to the proposed artifacts without changing approval or execution gates.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Standard library plus existing `pyyaml`

**Storage**: File-backed reports under `skills/<name>/` for new candidates and `skills/<name>/.candidate/` for regeneration/evolution candidates

**Testing**: `pytest`; compile validation with `python -m compileall`

**Target Platform**: Docker-first CLI application, also runnable directly on local Python

**Project Type**: Python CLI agent with skill framework

**Performance Goals**: Report writing adds negligible overhead relative to LLM generation and smoke tests

**Constraints**: No new frameworks or major dependencies; preserve approval ledger semantics; do not execute proposed or deprecated skills

**Scale/Scope**: Latest report per candidate is required; a global dashboard or searchable report database is out of scope

## Constitution Check

- **Minimal, targeted changes**: Pass. Add a focused reporting module in `py_mono/skill/` and call it from `generate_skill`.
- **Provider-agnostic core**: Pass. No changes to provider selection or model integrations.
- **Tool, skill, and playbook separation**: Pass. Reports are emitted from the skill lifecycle path and do not call tools directly.
- **Test coverage**: Pass. Add focused unit tests for report serialization and generator integration.
- **Incremental philosophy**: Pass. File-backed report state is sufficient for ISS-019 and avoids a dashboard or service.

## Project Structure

### Documentation (this feature)

```text
specs/016-lifecycle-state-reports/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── lifecycle-report.md
└── tasks.md
```

### Source Code

```text
py_mono/
└── skill/
    ├── lifecycle.py
    ├── diffing.py
    └── reporting.py

skills/
└── generate_skill/
    └── skill.py

tests/
├── test_skill_lifecycle_reporting.py
└── test_generate_skill.py
```

**Structure Decision**: Add report persistence as a skill framework helper, not as an agent-level responsibility. The generator already owns lifecycle assembly and candidate placement, so it is the narrowest integration point.

## Complexity Tracking

No constitution violations.
