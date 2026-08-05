# Tasks: Declare `pyyaml` as a direct dependency

**Input**: Design documents from `/specs/007-add-pyyaml-direct-dependency/`

All tasks below were already executed and verified.

## Phase 1: Setup

- [x] T001 Confirm all direct `import yaml` call sites via repo-wide search: found 4
      (`py_mono/skill/validator.py`, `py_mono/skill/base.py`,
      `py_mono/playbook/playbookregistry.py`, `skills/generate_playbook/skill.py`)

## Phase 2: User Story 1 - Installing declared dependencies is enough to run this project (Priority: P1)

- [x] T002 [US1] Add `"pyyaml"` to `pyproject.toml`'s `[project.dependencies]`, unpinned,
      matching the convention for other unpinned dependencies in the same list
- [x] T003 [US1] Run `uv lock` to regenerate `uv.lock` with `pyyaml` as a direct dependency
- [x] T004 [US1] Run the full test suite to confirm no regression introduced by this change
      alone (pre-existing, unrelated `ISS-005` failures are tracked and fixed separately in
      PR #96, not part of this change's scope)

## Dependencies & Execution Order

Single linear sequence — no parallelism needed for a change this small.
