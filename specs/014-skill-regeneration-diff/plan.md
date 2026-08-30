# Implementation Plan: Skill Regeneration Diff

**Branch**: `014-skill-regeneration-diff` | **Date**: 2026-08-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-skill-regeneration-diff/spec.md`

## Summary

Extend the post-`ISS-015` skill regeneration path so regenerated candidates show a diff against
the last approved baseline before the user approves anything. Keep diff generation as review
evidence only; the existing approval command remains the only path to approved execution.

## Technical Context

**Language/Version**: Python >=3.10

**Primary Dependencies**: Existing standard library and project modules; no new runtime
dependency expected.

**Storage**: Existing `skills/<skill_name>/` files and `skills/.approvals.json`; optional git
history lookup for approved baselines.

**Testing**: `pytest`; focused tests for baseline discovery, artifact diff rendering, and
approval-boundary regression.

**Target Platform**: Existing Docker-first Python CLI workflow.

**Project Type**: Single Python project with repo-level skill packages.

**Performance Goals**: Diff generation should be fast for normal skill files and should not call
the LLM.

**Constraints**: Do not auto-approve regenerated output. Do not implement production-failure
repair, lifecycle persistence/reporting polish, CLI/UX polish, signed packages, or isolated
workers in this slice.

**Scale/Scope**: Small M7 slice likely touching `skills/generate_skill/skill.py`, a focused
diff/baseline helper under `py_mono/skill/`, and tests.

## Constitution Check

- **Minimal, Targeted Changes**: PASS -- add review evidence around regeneration only.
- **Provider-Agnostic Core**: PASS -- no provider routing or model behavior changes.
- **Tool, Skill, and Playbook Separation**: PASS -- no direct tool-function execution.
- **Test Coverage for New Behavior**: PASS -- plan requires tests for diff and approval boundary.
- **Incremental Change Philosophy**: PASS -- failure-driven evolution remains a later issue.

No violations.

## Project Structure

```text
py_mono/skill/diffing.py                   # likely new: baseline and artifact diff helpers
skills/generate_skill/skill.py             # allow regeneration path to render diff evidence
tests/test_skill_diffing.py                # likely new helper tests
tests/test_generate_skill_regeneration.py  # likely new integration-style tests
```

**Structure Decision**: Put baseline/diff mechanics in `py_mono/skill/` and keep user-facing
orchestration in `generate_skill`.

## Complexity Tracking

No complexity exceptions.
