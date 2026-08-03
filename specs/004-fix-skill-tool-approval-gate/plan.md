# Implementation Plan: Fix Skill/Tool Approval Gate

**Branch**: `fix-skill-tool-approval-gate` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-fix-skill-tool-approval-gate/spec.md`

## Summary

Gate `py_mono/skill/base.py`'s `SkillRegistry.load()`/`reload_skill()` so `_load_skill_py()`
(which does `exec_module`) only runs when a skill's status is `approved` AND a new,
tracked approval-ledger entry's recorded `sha256` hash of `skill.py` matches its current
content — closing both "runs before approval" and "content changed after approval, still
trusted" in one mechanism. `/approve` (`py_mono/agent/agent.py`) re-validates current
`skill.py` via the existing, already-safe `validate_skill_py()` before writing the ledger
entry. A one-time auto-seed covers the 8 already-approved skills with zero disruption.
Dynamic tools get a new `ENABLE_DYNAMIC_TOOLS` opt-in (default false, mirroring
`ENABLE_SHELL_TOOL`'s established ISS-002 pattern) plus static validation before
`exec_module` and before `create_tool()` writes anything to disk.

## Technical Context

**Language/Version**: Python 3.10+ (matches this repo's `requires-python`)

**Primary Dependencies**: None new — `hashlib`, `json` (for the ledger) are stdlib; reuses
the existing `validate_skill_py`/`FORBIDDEN_PATTERNS` from `py_mono/skill/validator.py`.

**Storage**: A new small tracked JSON file (`skills/.approvals.json`) — the approval ledger.
No database.

**Testing**: `pytest`, new tests at `tests/test_skill_load_gating.py` (flat, matches
existing `tests/test_*.py` convention) and `tests/tools/test_tool_loader.py` (new file in
the existing `tests/tools/` dir), plus new assertions in `tests/tools/test_create_tool.py`.

**Target Platform**: Cross-platform (same as all prior features in this repo)

**Project Type**: Security fix within an existing monolith (`py_mono/`), not a new service

**Performance Goals**: Hashing a `skill.py` file and comparing two strings is negligible
cost, run only at load/reload/approve time, not per-invocation.

**Constraints**: Must not modify `SafeAgentTools`/`run_skill_safe` (`py_mono/skill/approval.py`)
or the tool-call dispatch loop in `agent.py` — this fix is about *what loads and when*, not
*what an already-approved, already-running skill can do*. Must not require individual
manual re-review of the 8 already-approved skills. No new external dependencies.

**Scale/Scope**: Small, targeted — one new small ledger file/helper, gated conditionals in
two existing functions, one new validation call in `/approve`, one new env var, static
validation added at two dynamic-tool call sites, one ADR correction.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Minimal, Targeted Changes** — PASS. No restructuring; the ledger is a small new
  file/helper alongside existing skill machinery, `SkillRegistry`'s existing methods gain a
  conditional, `/approve` gains one validation call, dynamic-tool loading gains the same
  gate-and-validate shape `ENABLE_SHELL_TOOL`/shell already established.
- **II. Provider-Agnostic Core** — N/A. No LLM provider code touched.
- **III. Tool, Skill, and Playbook Separation** — PASS. No change to `Tool.run(**kwargs)`
  or the skill/tool dispatch interface — only to whether a skill/tool's code is loaded
  (made callable) in the first place.
- **IV. Test Coverage for New Behavior** — PASS (planned). New tests at
  `tests/test_skill_load_gating.py`, `tests/tools/test_tool_loader.py`, extended
  `tests/tools/test_create_tool.py` — top-level, mirroring source layout, `test_*.py` named.
- **V. Incremental Change Philosophy** — PASS. Purely additive for the gating logic itself;
  the one existing-behavior change (dynamic tools off by default) mirrors the
  already-established, already-approved `ENABLE_SHELL_TOOL` precedent from ISS-002, and the
  8 existing approved skills are explicitly protected from disruption via auto-seed.

No violations requiring justification. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/004-fix-skill-tool-approval-gate/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── approval-gate-contract.md   # Phase 1 output
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
py_mono/skill/
├── base.py                     # MODIFIED — gate exec_module on approval-ledger match
├── approval_ledger.py          # NEW — read/write/seed the approval ledger
└── validator.py                # MODIFIED — export FORBIDDEN_PATTERNS for reuse by tool_loader.py

py_mono/agent/agent.py           # MODIFIED — _handle_skill_approve() re-validates + writes ledger
py_mono/config.py                # MODIFIED — new ENABLE_DYNAMIC_TOOLS
py_mono/main.py                  # MODIFIED — gate load_dynamic_tools() call on ENABLE_DYNAMIC_TOOLS
py_mono/tools/tool_loader.py     # MODIFIED — static validation before exec_module
py_mono/tools/create_tool.py     # MODIFIED — static validation before writing to disk

skills/.approvals.json           # NEW — tracked approval ledger (auto-seeded on first run)
docs/adr/ADR-013-*.md            # MODIFIED — correction note, not a new ADR

tests/test_skill_load_gating.py       # NEW
tests/tools/test_tool_loader.py       # NEW
tests/tools/test_create_tool.py       # MODIFIED — new assertions only
```

**Structure Decision**: Targeted change within existing `py_mono/skill/`, `py_mono/tools/`,
and `py_mono/agent/` — one new small module (`approval_ledger.py`) alongside existing skill
machinery, consistent with how `py_mono/llm/ollama_connectivity.py` was added as a small
sibling module in the Ollama feature. Tests land under this repo's existing flat top-level
`tests/` convention — no new `tests/skill/` subpackage.

## Complexity Tracking

*No violations — table not needed.*
