# Implementation Plan: Isolated Worker Execution

**Branch**: `iss-008-isolated-worker-execution` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/018-isolated-worker-execution/spec.md`

## Summary

Replace main-process execution of approved generated extensions with per-invocation subprocess workers. Skill registry loading will create skill proxies instead of importing approved modules; `run_skill_safe` will execute those proxies via a worker with JSON-line tool RPC. Dynamic tool loading will statically extract tool metadata and create worker-backed `Tool` proxies.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Standard library only

**Storage**: Existing `skills/`, `dynamic_tools/`, and approval ledger files

**Testing**: `pytest`; compile validation with `python -m compileall`

**Target Platform**: Docker-first CLI application, also runnable directly on local Python

**Project Type**: Python CLI agent with generated extension modules

**Performance Goals**: Worker startup overhead is acceptable for human-driven skill/tool commands

**Constraints**: No new frameworks; preserve `Tool.run(**kwargs)`; preserve approval ledger; do not execute proposed skills

**Scale/Scope**: One worker per extension invocation; no persistent worker pool

## Constitution Check

- **Minimal, targeted changes**: Pass. Add worker modules and route generated extension execution through them.
- **Provider-agnostic core**: Pass. No LLM provider changes.
- **Tool, skill, and playbook separation**: Pass. Tool RPC still invokes parent `Tool.run(**kwargs)`.
- **Test coverage**: Pass. Add worker tests and update approval/dynamic-tool tests.
- **Incremental philosophy**: Pass. Per-invocation subprocess avoids worker-pool complexity.

## Project Structure

### Documentation (this feature)

```text
specs/018-isolated-worker-execution/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── worker-rpc.md
└── tasks.md
```

### Source Code

```text
py_mono/
├── skill/
│   ├── approval.py
│   ├── base.py
│   └── worker.py
└── tools/
    ├── tool_loader.py
    └── worker.py

tests/
├── test_skill_worker.py
├── test_skill_load_gating.py
└── tools/test_tool_loader.py
```

**Structure Decision**: Keep skill worker execution under `py_mono/skill/` and dynamic-tool worker execution under `py_mono/tools/`, sharing only the JSON-line protocol shape.

## Complexity Tracking

No constitution violations.
