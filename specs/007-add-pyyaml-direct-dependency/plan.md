# Implementation Plan: Declare `pyyaml` as a direct dependency

**Branch**: `add-pyyaml-direct-dependency` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/007-add-pyyaml-direct-dependency/spec.md`

## Summary

Added `pyyaml` to the root `pyproject.toml`'s `dependencies` list (unpinned, matching the
convention already used for `requests`/`pandas`/`rich`) and regenerated `uv.lock`. Confirmed
four direct `import yaml` call sites (`py_mono/skill/validator.py`, `py_mono/skill/base.py`,
`py_mono/playbook/playbookregistry.py`, `skills/generate_playbook/skill.py`) before making the
change; none required a version pin.

## Technical Context

**Language/Version**: Python (repo `requires-python = ">=3.10"`, unchanged)

**Primary Dependencies**: `pyyaml` — was already present transitively via `litellm`/`fastmcp`;
now declared directly

**Storage**: N/A

**Testing**: No behavior change; existing suite re-run to confirm no regression from the
manifest/lockfile change alone

**Target Platform**: Unchanged

**Project Type**: Single project — manifest/lockfile change only

**Constraints**: Root `pyproject.toml`/`uv.lock` only; `kb-template/`'s independent
`pyproject.toml` (which already declares `pyyaml` on its own) explicitly not touched

**Scale/Scope**: Minimal — one dependency line, one lockfile regeneration

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS — single-line dependency addition, no
  restructuring.
- **Principle IV (Test Coverage for New Behavior)**: N/A — no new behavior; existing suite is
  the regression check.
- **Principle V (Incremental Change Philosophy)**: PASS — purely additive, no existing interface
  changed.

No violations.

## Project Structure

### Source Code (repository root)

```text
pyproject.toml   # + "pyyaml" under [project] dependencies
uv.lock          # regenerated via `uv lock`
```

**Structure Decision**: No new structure — manifest/lockfile change only.
