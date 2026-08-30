# Implementation Plan: Failure-Driven Skill Evolution

**Branch**: `015-failure-driven-skill-evolution` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/015-failure-driven-skill-evolution/spec.md`

## Summary

Add a proposal-only path that uses a real approved-skill failure as context for generating a
revised skill candidate. The candidate must re-enter the `ISS-015` lifecycle and remain proposed
until the user explicitly approves it.

## Technical Context

**Language/Version**: Python >=3.10

**Primary Dependencies**: Existing project modules; no new runtime dependency expected.

**Storage**: Existing telemetry/failure records if sufficient, with minimal extension only if
needed to capture actionable failure context.

**Testing**: `pytest`; tests for failure-context lookup, proposal generation, lifecycle reuse, and
approval-boundary regression.

**Target Platform**: Existing Docker-first Python CLI workflow.

**Project Type**: Single Python project with repo-level skill packages.

**Performance Goals**: Uses one failure context and normal generation lifecycle; no background
repair loop.

**Constraints**: Never self-authorize. Do not silently mutate approved skill behavior. Do not add
persistent lifecycle dashboards, CLI/UX polish, signed packages, or isolated workers in this
slice.

**Scale/Scope**: Medium M7 slice after `ISS-015`; likely touches failure capture/telemetry,
skill-generation prompting/orchestration, and tests.

## Constitution Check

- **Minimal, Targeted Changes**: PASS -- scoped to proposal generation from failures.
- **Provider-Agnostic Core**: PASS -- failure context may include provider/model names, but no
  provider-specific behavior is planned.
- **Tool, Skill, and Playbook Separation**: PASS -- generated fixes go through normal skill paths.
- **Test Coverage for New Behavior**: PASS -- plan requires tests for context, lifecycle reuse,
  and approval boundary.
- **Incremental Change Philosophy**: PASS -- dashboards, CLI polish, provenance, and isolation
  stay separate.

No violations.

## Project Structure

```text
py_mono/skill/evolution.py                 # likely new: failure-context and proposal helpers
py_mono/skill/telemetry.py                 # possible minimal extension for failure context
skills/generate_skill/skill.py             # likely reuse lifecycle generation path
tests/test_skill_evolution.py              # likely new helper tests
tests/test_generate_skill_evolution.py     # likely new integration-style tests
```

**Structure Decision**: Keep failure-driven evolution in the skill framework and reuse
`generate_skill` lifecycle mechanics instead of creating a self-patching execution path.

## Complexity Tracking

No complexity exceptions.
