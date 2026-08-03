# Contract: Skill/tool approval gate

No HTTP/CLI surface changes beyond `/approve`'s existing behavior gaining new failure
modes and `/reload_tools`'s existing behavior gaining a new "disabled" message. This
documents the function-level and CLI-level contracts.

## `SkillRegistry.load()` / `reload_skill(name)`

**Location**: `py_mono/skill/base.py`

| Behavior | Contract |
|---|---|
| Metadata parsing | Unchanged — always happens, never executes code, always available via `list_skills()`/`get_skill_md()` regardless of load state |
| Code execution (`exec_module`) | Happens only when `status == "approved"` AND the ledger's hash for this skill matches current `skill.py` content |
| Auto-seed | On first encounter of an `approved` skill with no ledger entry, a `seeded: true` entry is written automatically before the load-gate check re-evaluates (so it loads on this same call) |
| Failure mode | A skill that fails the gate is simply not loaded — no exception raised, consistent with today's `_load_skill_py` returning `None` on failure |

## `/approve <skill_name>` (`_handle_skill_approve` in `py_mono/agent/agent.py`)

| Input state | Behavior |
|---|---|
| `skill.py` fails `validate_skill_py` | SKILL.md untouched, ledger untouched, a clear rejection message returned naming the validation failure, `reload_skill` never called |
| `skill.py` passes `validate_skill_py` | SKILL.md's `status` rewritten to `approved` (unchanged mechanism), ledger entry written/updated with current hash (`seeded: false`), `reload_skill(name)` called — now succeeds in loading per the gate above |

**Stability**: `/approve`'s existing success-path output shape is unchanged; the new
failure mode (validation rejection) is additive, not a breaking change to any existing
successful-approval behavior.

## `ENABLE_DYNAMIC_TOOLS` gate

**Location**: `py_mono/config.py`, consumed in `py_mono/main.py::main()` and
`py_mono/agent/agent.py::_reload_dynamic_tools()`

| `ENABLE_DYNAMIC_TOOLS` | `load_dynamic_tools()` called | Result |
|---|---|---|
| unset / falsy (default) | No | `dynamic_tools = []`; `/reload_tools` reports the capability is disabled instead of silently loading nothing |
| truthy | Yes | Behaves as today, plus the new per-file static validation below |

## `load_dynamic_tools()` static validation

**Location**: `py_mono/tools/tool_loader.py`

| File content | Outcome |
|---|---|
| Contains a `FORBIDDEN_PATTERNS` match or fails `ast.parse` | Skipped, a warning is logged (same style as the existing `except Exception` branch) — `exec_module` never runs for this file |
| Clean | Loaded exactly as today |

**Stability**: this check only ever *removes* files from what gets loaded relative to
today's behavior — it never changes how a file that passes is subsequently treated.

## `create_tool(name, code)`

**Location**: `py_mono/tools/create_tool.py`

| `code` | Outcome |
|---|---|
| Contains a forbidden pattern or fails to parse | Nothing written to disk; an error string is returned, same shape as the existing `"Invalid tool name."` early return |
| Clean | Written to `dynamic_tools/{name}.py` exactly as today |
