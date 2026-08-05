# Feature Specification: Declare `pyyaml` as a direct dependency

**Feature Branch**: `add-pyyaml-direct-dependency`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work)

**Input**: User description: "Fix ISS-006 — `pyyaml` is imported directly by
`py_mono/skill/validator.py`, `py_mono/skill/base.py`, `py_mono/playbook/playbookregistry.py`,
and `skills/generate_playbook/skill.py`, but is only ever resolved transitively (via
`litellm`/`fastmcp`), never declared as a direct dependency in the root `pyproject.toml`. See
`docs/ISSUES.md` ISS-006."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Installing this project's declared dependencies is enough to run it (Priority: P1)

A contributor installs this project from `pyproject.toml` alone. Every module the project
imports directly should be guaranteed present by that install, not by an incidental transitive
dependency of an unrelated package that could be upgraded or replaced later.

**Why this priority**: This is a latent breakage risk — if `litellm` or `fastmcp` ever drop or
change their `pyyaml` dependency, four files that `import yaml` directly would start failing
with no warning from this project's own declared dependencies.

**Independent Test**: Confirm `pyyaml` appears in `pyproject.toml`'s direct `dependencies` list
and that `uv lock` resolves cleanly with it present.

**Acceptance Scenarios**:

1. **Given** a fresh environment built only from this project's `pyproject.toml`, **When**
   any module that does `import yaml` is imported, **Then** the import succeeds without relying
   on another package's transitive dependency.

### Edge Cases

- Does this change affect `kb-template/`'s own dependency declarations? No — `kb-template/` has
  its own separate `pyproject.toml` that already declares `pyyaml` independently; this issue is
  scoped to the root project only (a prior attempt to bundle this fix into the `kb-template`
  branch was reverted for exactly this reason — see `docs/ISSUES.md` ISS-006 history).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The root `pyproject.toml` MUST declare `pyyaml` as a direct dependency.
- **FR-002**: `uv.lock` MUST be regenerated to reflect the updated direct-dependency graph.
- **FR-003**: The change MUST NOT touch `kb-template/`'s independent dependency declarations.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `pyyaml` appears under `[project.dependencies]` in the root `pyproject.toml`.
- **SC-002**: `uv lock` resolves without error after the change.
- **SC-003**: The existing test suite's pass/fail outcome is unaffected by this change alone
  (this is a manifest/lockfile change, not a behavior change).

## Assumptions

- `pyyaml`'s version is left unpinned (matching this project's existing convention for most
  dependencies in `pyproject.toml`, e.g. `requests`, `pandas`, `rich`), since no specific version
  constraint has ever been required by the four call sites that use it.
