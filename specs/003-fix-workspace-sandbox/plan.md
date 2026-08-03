# Implementation Plan: Fix Workspace Sandbox Escape

**Branch**: `fix-workspace-sandbox` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-fix-workspace-sandbox/spec.md`

## Summary

Replace `py_mono/utils/path_utils.py`'s string-prefix path check with real path containment
(`Path.is_relative_to()`), checked against a list of allowed roots (`WORKSPACE_ROOT` plus a
new, empty-by-default `ADDITIONAL_ALLOWED_PATHS` env-configured list) — fixes all four
existing file-tool callers for free. Gate `py_mono/tools/shell.py`'s inclusion in the
default tool set behind a new `ENABLE_SHELL_TOOL` opt-in (default false), add a subprocess
timeout, and correct its description to state plainly it's a best-effort blocklist, not a
sandbox — none of this narrows shell's actual reach once enabled. Change
`docker-compose.yml`'s full-repo mount to read-only, since the three directories anything
actually writes to at runtime already have their own separate read-write mounts. Correct
`docs/adr/ADR-001-safe-execution-of-tools.md`'s claims to match the fixed, real behavior.

## Technical Context

**Language/Version**: Python 3.10+ (matches this repo's `requires-python`)

**Primary Dependencies**: None new — `pathlib`, `subprocess`, `os` are all stdlib, already
in use in the files being modified.

**Storage**: N/A — configuration via environment variables only

**Testing**: `pytest`, new tests at `tests/utils/test_path_utils.py` (new dir, mirrors
`py_mono/utils/`) and `tests/tools/test_shell.py` (existing dir), per Constitution
Principle IV.

**Target Platform**: Cross-platform (Windows dev host, Linux container at runtime —
symlink-escape test is skipped on `win32` since symlink creation needs Developer Mode or
elevation not guaranteed in this dev environment; real coverage holds via the Linux
container, which is how this app actually runs)

**Project Type**: Security fix within an existing monolith (`py_mono/`), not a new service

**Performance Goals**: No measurable performance requirement — path containment checks and
the shell-availability gate are both cheap, synchronous, one-time-per-call operations with
no added I/O.

**Constraints**: Must not modify `py_mono/agent/agent.py`'s command dispatch, dynamic-tool
loading, or the execution loop; no new dependencies; shell's actual reach (once enabled)
must not change; `ADDITIONAL_ALLOWED_PATHS` must default to empty so behavior is unchanged
for anyone not using it.

**Scale/Scope**: Small, targeted — one corrected helper function, one new small env-driven
allowlist, one gating extraction in `main.py`, one Docker mount change, one ADR correction.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Minimal, Targeted Changes** — PASS. No restructuring; `resolve_safe_path` gains a
  corrected check and a second allowed-roots source, `main.py` gains one extracted function
  (mirroring `load_mcp_tools()`/`load_skills()`, an existing pattern in the same file, not a
  new one), `shell.py` gains a timeout and corrected description, `docker-compose.yml` gains
  a mount-mode suffix and two env vars. No new frameworks/dependencies.
- **II. Provider-Agnostic Core** — N/A. This feature doesn't touch LLM provider code.
- **III. Tool, Skill, and Playbook Separation** — PASS. No new tool, skill, or playbook;
  `shell_tool`'s existing `Tool.run(**kwargs)` interface is unchanged, only its
  availability and description.
- **IV. Test Coverage for New Behavior** — PASS (planned). New tests at
  `tests/utils/test_path_utils.py` and `tests/tools/test_shell.py`, top-level, mirroring
  source layout, `test_*.py` named.
- **V. Incremental Change Philosophy** — PASS. The one existing-behavior change (shell tool
  changing from always-on to opt-in) is the explicitly-requested, confirmed fix for the
  security issue this feature exists to close — not an incidental break.

No violations requiring justification. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/003-fix-workspace-sandbox/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── path-and-shell-contract.md   # Phase 1 output — resolve_safe_path + shell gating contract
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
py_mono/utils/path_utils.py       # MODIFIED — real containment + allowed-roots list
py_mono/config.py                  # MODIFIED — ENABLE_SHELL_TOOL, ADDITIONAL_ALLOWED_PATHS
py_mono/tools/shell.py             # MODIFIED — timeout, honest description
py_mono/main.py                    # MODIFIED — extracted, gated build_base_tools()

docker-compose.yml                  # MODIFIED — .:/app:ro, two new env vars
.env.example                        # MODIFIED — commented-out examples
docs/adr/ADR-001-safe-execution-of-tools.md   # MODIFIED — corrected claims, Accepted

tests/utils/                        # NEW — mirrors py_mono/utils/
└── test_path_utils.py
tests/tools/
└── test_shell.py                   # NEW — mirrors py_mono/tools/ (dir already exists)
```

**Structure Decision**: Targeted change within existing `py_mono/utils/`, `py_mono/tools/`,
and `py_mono/` root — no new top-level application structure needed. Tests land under this
repo's existing top-level `tests/` convention; only `tests/utils/` is a new directory
(`tests/tools/` already exists from `test_create_tool.py`).

## Complexity Tracking

*No violations — table not needed.*
