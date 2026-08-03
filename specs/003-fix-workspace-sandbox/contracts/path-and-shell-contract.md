# Contract: `resolve_safe_path` + shell tool availability

This feature's interfaces are two Python function contracts (no HTTP/CLI surface changes)
plus one container-runtime contract.

## `resolve_safe_path(user_path: str) -> Path`

**Location**: `py_mono/utils/path_utils.py`

**Callers** (unchanged, no code changes needed in any of them): `read_file.py`,
`write_file.py`, `edit_file.py`, `list_files.py`.

| Behavior | Contract |
|---|---|
| Accepts | A path inside `WORKSPACE_ROOT` or any entry in `ADDITIONAL_ALLOWED_PATHS`, by real filesystem location (not textual form) |
| Rejects | Everything else, including sibling-prefix-collision paths, `../` traversal, and symlinks resolving outside all allowed roots |
| On rejection | Raises `ValueError` with a message naming the rejected path — uncaught, propagates to the caller exactly as before this fix |
| On acceptance | Returns the fully-resolved `Path` |

**Stability**: The exception type (`ValueError`) and the fact that a rejection is raised
rather than returned are both *pre-existing* behavior, unchanged by this fix — a caller
relying on catching `ValueError` today continues to work identically.

## Shell tool availability — `build_base_tools(enable_shell: Optional[bool] = None) -> list`

**Location**: `py_mono/main.py`

| Behavior | Contract |
|---|---|
| `enable_shell=None` (default) | Reads `ENABLE_SHELL_TOOL` from the environment |
| `enable_shell=True`/`False` | Overrides the environment value — used by tests |
| Returned list | Same six tools as today, plus `shell_tool` appended only when the effective flag is truthy |

**Stability**: `shell_tool`'s own interface (`name="shell"`, `parameters={"command": ...}`,
`run(**kwargs)`) is completely unchanged — only whether it appears in the list this
function returns changes.

## Shell command execution — `run_shell(command: str) -> str`

**Location**: `py_mono/tools/shell.py`

| Behavior | Contract (unchanged from today) |
|---|---|
| Reach | Whatever the container process's OS permissions allow — not narrowed or widened by this fix |
| Blocklist | `FORBIDDEN_PATTERNS` substring match — defense-in-depth only, unchanged |
| **New**: Timeout | `DEFAULT_SHELL_TIMEOUT_SECONDS = 30` — a command still running after this long is terminated, `subprocess.TimeoutExpired` caught and returned as `"[TOOL ERROR] Command timed out after 30s: '<command>'"` |
| **New**: Description | States explicitly this is a best-effort filter, not a content sandbox |

## Container runtime — `docker-compose.yml`'s `py-coding-agent` service

| Mount | Before | After |
|---|---|---|
| `.:/app` | read-write | **read-only** |
| `./workspace:/workspace` | read-write | read-write (unchanged) |
| `./dynamic_tools:/app/dynamic_tools` | read-write | read-write (unchanged) |
| `./skills:/app/skills` | read-write | read-write (unchanged) |

**Stability**: Anything currently writing only to `workspace/`, `dynamic_tools/`, or
`skills/` is unaffected. Anything that was (incorrectly, or by accident) relying on write
access to the mounted source outside those three subdirectories will now fail with a
read-only-filesystem error — this is the intended effect of the fix, not a regression.
