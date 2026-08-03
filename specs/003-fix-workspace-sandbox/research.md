# Phase 0 Research: Fix Workspace Sandbox Escape

No `NEEDS CLARIFICATION` markers remained — the prior planning conversation with the user
(including two live demonstrations of the actual bugs against the real, pre-fix code)
already resolved every open design question. This file records the decisions for the record.

## Decision: `Path.is_relative_to()` over string-prefix or trailing-separator patching

**Decision**: Replace `str(path).startswith(str(WORKSPACE_ROOT))` with
`path.is_relative_to(root)`, checked against a list of allowed roots.

**Rationale**: Live-confirmed during planning: `resolve_safe_path('../workspace_evil')`
resolved to `/workspace_evil` and was **accepted** under the current code — a sibling
directory whose name textually starts with the workspace root's own text passes a pure
string-prefix check. `Path.is_relative_to()` checks real path containment instead. Both
`WORKSPACE_ROOT` and the candidate path are already `.resolve()`'d (symlinks followed)
before the check runs, so this also correctly rejects symlink-based escapes.

**Alternatives considered**:
- *Append a trailing separator before the string comparison*
  (`str(path).startswith(str(WORKSPACE_ROOT) + "/")`) — this was raised directly during
  planning and would close the specific sibling-prefix bug, but has its own edge case:
  a path exactly equal to `WORKSPACE_ROOT` itself (no subpath) would incorrectly fail this
  check, since nothing follows the root to match the trailing separator. `is_relative_to`
  handles the exact-root case correctly natively (a path is always relative to itself) and
  avoids further string-comparison pitfalls (OS-specific separators, case sensitivity).
  Rejected in favor of the more robust, purpose-built pathlib method — this is exactly what
  the original audit recommended.

## Decision: Additional-allowed-paths as a flat comma-separated env var, empty by default

**Decision**: `ADDITIONAL_ALLOWED_PATHS` env var, comma-separated absolute paths, parsed
once into a list of `.resolve()`'d `Path` objects in `config.py`. `resolve_safe_path` checks
containment against `[WORKSPACE_ROOT] + ADDITIONAL_ALLOWED_PATHS`.

**Rationale**: Directly requested by the user during planning — after seeing that shell
already has broad reach and file tools are correctly confined, the user wanted a deliberate,
explicit way to grant file-tool access to specific additional locations later, without
reopening this fix. Empty by default means zero behavior change for anyone not using it —
confirmed as a hard requirement.

**Alternatives considered**:
- *A single `OLLAMA_BACKENDS`-style structured (JSON/YAML) env var* — rejected: this repo
  has no precedent for structured env-var values (confirmed via the dual-Ollama-backend
  feature, which also chose flat, paired env vars over a structured blob for the same
  reason); a flat comma-separated list is simpler to read, write, and override one entry of.
- *A per-call runtime grant (e.g. an approval prompt each time a tool wants to go outside
  the workspace)* — rejected as out of scope: the user specifically wants a static,
  deliberate, pre-configured allowlist, not an interactive runtime negotiation — the latter
  would also touch `py_mono/agent/agent.py`'s command dispatch, explicitly out of scope.

## Decision: Shell tool gated behind `ENABLE_SHELL_TOOL`, reach unchanged

**Decision**: New `ENABLE_SHELL_TOOL` env var (default `false`, truthy-string parsed),
gating whether `shell_tool` is included in the assembled tool set. When enabled, the tool's
actual behavior (what commands can do, where they can reach) is completely unchanged from
today.

**Rationale**: Live-confirmed during planning: `ls /` and `cat /etc/os-release` both
succeeded via the shell tool with zero restriction under the current, unfixed code — shell
was never confined to `/workspace` to begin with, and true content-level sandboxing would
require OS-level isolation (out of scope, per the audit's own framing of it as a
materially larger alternative). Given that, the achievable, meaningful fix is gating
*availability*, not attempting (and failing) to retroactively confine *reach*. The user
confirmed this explicitly — enabling shell doesn't expand or restrict where it can go, it
only changes whether it exists as a capability at all, and they said they'd set the env var
themselves regardless.

**Alternatives considered**:
- *Keep shell enabled by default, harden only (timeout, better blocklist)* — this was
  presented to the user as an explicit alternative and rejected: it wouldn't close the
  escape vector, only document it as accepted risk, and the audit's own recommendation is
  to remove it from the default set.
- *Attempt real content-level shell sandboxing now* (dedicated restricted container,
  seccomp, chroot) — rejected: a materially larger infrastructure project, explicitly out
  of scope for this fix, tracked as a possible future, separate undertaking if ever pursued.

## Decision: `build_base_tools(enable_shell: Optional[bool] = None)` over `importlib.reload`

**Decision**: Extract tool assembly into a plain function accepting an optional override
parameter, rather than relying on `importlib.reload()` to re-evaluate env-var-derived
module constants between test cases.

**Rationale**: `ENABLE_SHELL_TOOL` is read once at import time in `config.py`; testing both
the enabled and disabled states in one test session requires either reloading modules
(fragile — reload can cause subtle double-import issues if other modules hold references to
the pre-reload module object) or accepting an explicit override at the call site. The
override parameter is simpler, more conventional, and avoids reload entirely, at the cost
of a one-argument function signature addition — a clearly better trade than reload
fragility for a function this small.

**Alternatives considered**:
- *`importlib.reload(config)` / `importlib.reload(main)` per test* — works, but is a
  known-fragile pattern; rejected in favor of the override parameter once both were on the
  table (this exact trade-off was flagged during planning and resolved in the override
  parameter's favor).

## Decision: Docker mount narrowed to `:ro`, not removed

**Decision**: `docker-compose.yml`'s `.:/app` becomes `.:/app:ro`. The three separately
specified rw mounts (`workspace/`, `dynamic_tools/`, `skills/`) are untouched.

**Rationale**: Confirmed via reading the `Dockerfile`: the image already `COPY`s the full
repo in at build time and installs it, so the bind mount's only real purpose at runtime is
live-edit development, not making the app function. Confirmed via reading
`create_tool.py` (writes only under `dynamic_tools/`), `uv_tool.py` (installs via
`--system`, into site-packages, not under `/app` at all), and the skill-approval code path
(writes only under `skills/*/SKILL.md`) that nothing legitimately needs write access to `/app`
outside those three already-separately-mounted subdirectories. Docker bind mounts support a
read-only parent with read-write nested sub-paths, which is exactly the existing shape of
this compose file already.

**Alternatives considered**:
- *Remove the `.:/app` mount entirely* — rejected: this would break live-edit development
  (a human editing source on the host and expecting the running container to see the
  change without a rebuild), which the read-write version currently supports and nothing in
  the fix requires removing; `:ro` preserves that host-edit-visibility while closing the
  actual write-access gap.
