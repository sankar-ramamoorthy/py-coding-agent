# Quickstart: Fix Workspace Sandbox Escape

Validation scenarios proving the feature works end-to-end. See `data-model.md` for the
resolution rules and `contracts/path-and-shell-contract.md` for the full function contracts.

## Prerequisites

- Repo checked out on `fix-workspace-sandbox` after `/speckit-implement` has landed the code.
- Docker available for the real-container scenarios (mount/shell-gating checks).

## Automated (mocked where needed) — run first

```
uv run pytest tests/utils/test_path_utils.py tests/tools/test_shell.py -v
```
**Expected**: all pass (symlink-escape test skipped on `win32`, real coverage lives in the
Linux container path).

## Scenario 1: Sibling-directory prefix collision rejected (FR-001, SC-001)

```python
from py_mono.utils.path_utils import resolve_safe_path
resolve_safe_path("../workspace_evil")
```
**Expected**: raises `ValueError` — this is the audit's own literal probe, live-confirmed
to *fail* (i.e. be incorrectly accepted) before this fix; must now correctly reject.

## Scenario 2: `../` traversal and symlink escape rejected (FR-002, FR-003)

Attempt `resolve_safe_path("../../etc/passwd")` and, on a POSIX system, a symlink placed
inside the workspace pointing outside it — both must raise `ValueError`.

## Scenario 3: Genuine in-workspace path still works (FR-004)

`resolve_safe_path("some/real/file.txt")` for a file that actually exists under
`WORKSPACE_ROOT` — must succeed exactly as before.

## Scenario 4: Additional allowed directory (FR-005, FR-006, SC-002)

With `ADDITIONAL_ALLOWED_PATHS` unset (default): confirm a path outside `WORKSPACE_ROOT` is
still rejected exactly as in Scenario 1 — no behavior change.

With `ADDITIONAL_ALLOWED_PATHS=/some/other/dir` set: confirm a path inside `/some/other/dir`
is now accepted, and a path outside both `WORKSPACE_ROOT` and `/some/other/dir` is still
rejected.

## Scenario 5: Shell tool absent by default, present when enabled (FR-007, FR-008, SC-003)

```
docker compose run --rm py-coding-agent python -c "from py_mono.main import build_base_tools; print({t.name for t in build_base_tools()})"
```
**Expected**: `"shell"` absent from the printed set with `ENABLE_SHELL_TOOL` unset. Repeat
with `ENABLE_SHELL_TOOL=true docker compose run --rm ...` — `"shell"` present.

## Scenario 6: Shell timeout (FR-009, SC-004)

With shell enabled, run a command that would hang forever (e.g. `sleep 60`) — confirm it's
terminated at 30 seconds with a `[TOOL ERROR] Command timed out...` message, not left
hanging.

## Scenario 7: Shell's reach is unchanged (FR-011)

With shell enabled, `ls /` and `cat /etc/os-release` — confirmed during planning to succeed
under the pre-fix code; must still succeed identically post-fix (this fix does not attempt
to narrow shell's reach, only its default availability).

## Scenario 8: Read-only source mount (FR-012, SC-005)

Rebuild (`docker compose up -d --build`, mount changed), then inside the running container:
- Create a dynamic tool, approve a skill, write a file under `/workspace`, and
  `uv pip install --system` a small package — all four must still succeed (their write
  targets are the three separately-mounted rw subdirectories, or outside `/app` entirely
  for the `uv` case).
- Attempt to write directly to a file under `/app` outside those three subdirectories (e.g.
  `/app/py_mono/main.py`) — must now fail with a read-only-filesystem error, where it would
  have silently succeeded before this fix.

## Repo-level regression checks

```
python -m compileall -q py_mono
pytest
```
**Expected**: all pass; the two pre-existing `ISS-005` failures remain exactly as
documented (not fixed here, not worsened).
