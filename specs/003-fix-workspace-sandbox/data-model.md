# Phase 1 Data Model: Fix Workspace Sandbox Escape

## Allowed roots (not a persisted entity — resolved at import time from config)

| Field | Source | Notes |
|-------|--------|-------|
| `WORKSPACE_ROOT` | `WORKSPACE_ROOT` env var, default `/workspace` | Always the first allowed root; unchanged from today. |
| `ADDITIONAL_ALLOWED_PATHS` | `ADDITIONAL_ALLOWED_PATHS` env var, comma-separated absolute paths | Empty list by default. Each entry `.resolve()`'d once at parse time. |

`allowed_roots = [WORKSPACE_ROOT] + ADDITIONAL_ALLOWED_PATHS` — computed inside
`resolve_safe_path` at call time (referencing the module-level names), not cached
separately, so tests can `monkeypatch.setattr` either independently.

## `resolve_safe_path(user_path: str) -> Path`

| Input | Output | Rule |
|---|---|---|
| Path resolves inside `WORKSPACE_ROOT` | Returns the resolved `Path` | `path.is_relative_to(WORKSPACE_ROOT)` is `True` |
| Path resolves inside any entry of `ADDITIONAL_ALLOWED_PATHS` | Returns the resolved `Path` | `path.is_relative_to(entry)` is `True` for at least one entry |
| Path resolves outside all allowed roots | Raises `ValueError` | No allowed root contains the resolved path |
| Path is a symlink resolving outside all allowed roots | Raises `ValueError` | `.resolve()` follows the symlink before the containment check runs |
| Path exactly equals an allowed root | Returns the resolved `Path` | A path is always relative to itself |

Exception propagation: `ValueError`, uncaught by this function or its four existing callers
(`read_file.py`, `write_file.py`, `edit_file.py`, `list_files.py`) — unchanged from today;
this fix only changes which paths are correctly classified as allowed, not how a rejection
is communicated.

## Shell tool gating (not a persisted entity — resolved at import time / call time)

| Field | Source | Notes |
|---|---|---|
| `ENABLE_SHELL_TOOL` | `ENABLE_SHELL_TOOL` env var, truthy-string parsed | Default `False`. |
| `build_base_tools(enable_shell)` | `enable_shell` param, defaults to reading `ENABLE_SHELL_TOOL` if `None` | Returns the tool list, with `shell_tool` appended only if the effective flag is truthy. |

| `enable_shell` argument | `ENABLE_SHELL_TOOL` env | Result |
|---|---|---|
| `None` (default) | unset / falsy | `shell` absent |
| `None` (default) | truthy | `shell` present |
| `True` (explicit override) | (ignored) | `shell` present |
| `False` (explicit override) | (ignored) | `shell` absent |

## Shell command execution (unchanged behavior, just gated availability)

| Field | Before this fix | After this fix |
|---|---|---|
| Availability | Always present in `base_tools` | Present only if `ENABLE_SHELL_TOOL` (or override) is truthy |
| Timeout | None (subprocess could hang indefinitely) | `DEFAULT_SHELL_TIMEOUT_SECONDS = 30`, raises `subprocess.TimeoutExpired`, caught and returned as a `[TOOL ERROR]` string |
| Reach (what a command can read/write/execute) | Unrestricted (container filesystem permissions apply) | **Unchanged** — this fix does not narrow or widen reach |
| Description shown to the assistant | Implies safety via blocklist | States plainly: best-effort filter, not a content sandbox |

## State transition: `docs/adr/ADR-001-safe-execution-of-tools.md`

```text
Status: Proposed
        │  this fix corrects the document's factual claims to match
        │  the now-fixed real behavior
        ▼
Status: Accepted
```
Not a code entity, but tracked here since the plan explicitly updates it in place rather
than creating a new ADR.
