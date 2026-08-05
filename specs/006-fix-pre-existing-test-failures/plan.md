# Implementation Plan: Fix pre-existing test failures

**Branch**: `fix-pre-existing-test-failures` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/006-fix-pre-existing-test-failures/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

Three independent, unrelated pre-existing test failures, root-caused separately: (1) the
`listallpy` skill bypassed `context.agent_tools` and walked the real filesystem directly,
violating ADR-016 and defeating its own tests' mocks; (2) the skill-approval hash ledger
(ADR-013/ISS-003) hashed raw on-disk bytes, which git's `core.autocrlf` rewrites per checkout
platform even for byte-identical tracked content — confirmed this would already break 7 of 9
approved skills' approval status the moment CI (ISS-012, same milestone) runs on a Linux
runner; (3) `create_tool` had two independent message/contract mismatches against its own
tests, unrelated to (1) or (2). Fixed by: routing `listallpy` through the tool abstraction,
normalizing line endings before hashing in `approval_ledger.hash_file()` (and regenerating the
ledger under the fixed algorithm), and correcting `create_tool`'s messages plus the two stale
test expectations that didn't match its actual (intentional, already-relied-upon-elsewhere)
wrapped-`Tool` contract.

## Technical Context

**Language/Version**: Python 3.13 locally (`.venv`), repo declares `requires-python = ">=3.10"` — unchanged

**Primary Dependencies**: None new — uses only `hashlib`, `json`, stdlib `pathlib`, already-present `py_mono.tools.tool.Tool`

**Storage**: `skills/.approvals.json` (existing flat JSON ledger) — regenerated in place under the fixed hashing scheme, no schema change

**Testing**: `pytest`, existing mock-based style (`Tool(name, description, lambda ...)` fixtures already used throughout `tests/`) — no real filesystem or network access needed for new tests

**Target Platform**: Cross-platform by requirement — this fix exists specifically because the previous behavior was platform-dependent (native Windows dev checkout vs. Linux CI/Docker checkout) when it should not have been

**Project Type**: Single project (existing agent codebase; no new project/package)

**Performance Goals**: N/A — no hot path affected; hashing a skill.py file at load/approve time is not performance-sensitive

**Constraints**: Fix confined to `skills/listallpy/skill.py`, `py_mono/skill/approval_ledger.py`, `skills/.approvals.json`, and `py_mono/tools/create_tool.py` — no other skill, tool, or the approval-gate's actual trust boundary touched

**Scale/Scope**: Small — one skill file, one ledger-hashing function, one regenerated ledger (9 entries), one tool's two message strings, two updated tests, one new test file (3 tests)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Minimal, Targeted Changes)**: PASS — each of the three fixes is confined to the
  exact file(s) responsible for its failure. No restructuring; `hash_file()`'s fix is a one-line
  normalization added to an existing function, not a new abstraction.
- **Principle II (Provider-Agnostic Core)**: N/A — no LLM provider code touched.
- **Principle III (Tool, Skill, and Playbook Separation)**: PASS, and directly *enforced* by
  this fix — `listallpy`'s bug was exactly a violation of this principle (direct filesystem
  access instead of `context.agent_tools`); the fix brings it into compliance rather than
  working around the violation.
- **Principle IV (Test Coverage for New Behavior)**: PASS — `tests/test_approval_ledger.py`
  added (3 tests: CRLF/LF equivalence, approval surviving simulated re-checkout, genuine content
  change still correctly invalidating approval). `listallpy`'s existing tests already covered
  the correct behavior; no test changes were needed there, only the implementation.
- **Principle V (Incremental Change Philosophy)**: PASS — `create_tool`'s wrapped-`Tool`
  contract (used by 3 already-passing tests) was treated as the deliberate, existing behavior;
  the two stale tests were corrected to match it rather than changing production behavior to
  satisfy tests nothing else depends on.

No violations. Complexity Tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/006-fix-pre-existing-test-failures/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command) — skipped, no external interface
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
skills/listallpy/skill.py            # fixed: use context.agent_tools["list_files"]
py_mono/skill/approval_ledger.py     # fixed: hash_file() normalizes line endings
skills/.approvals.json               # regenerated: all 9 entries re-hashed
py_mono/tools/create_tool.py         # fixed: two message strings
tests/tools/test_create_tool.py      # updated: 2 tests corrected to match actual contract
tests/test_approval_ledger.py        # new: 3 tests for the line-ending fix
```

**Structure Decision**: Single existing project (`py_mono/`, `skills/`, `tests/` at repo root,
already established layout) — no new structure introduced. Tests added under the existing flat
`tests/` convention (mirrors `tests/test_skill_approval.py`, `tests/test_skill_load_gating.py`
already living directly under `tests/` rather than a `tests/skill/` subdirectory).

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations — table not applicable.
