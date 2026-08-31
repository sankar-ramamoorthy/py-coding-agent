# Implementation Plan: Lifecycle CLI Review Polish

**Branch**: `iss-019-lifecycle-cli-polish` | **Date**: 2026-08-31 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/017-lifecycle-cli-review/spec.md`

## Summary

Add a small CLI review surface over `ISS-018` lifecycle reports. The agent will recognize `/skill review <name>`, render report JSON or Markdown fallback, mark pending candidates in list/help output, and clarify candidate promotion/rejection messages during approval.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: Standard library plus existing project modules

**Storage**: Existing `lifecycle_report.md` and `lifecycle_report.json` files

**Testing**: `pytest`; compile validation with `python -m compileall`

**Target Platform**: Docker-first CLI application, also runnable directly on local Python

**Project Type**: Python CLI agent with skill framework

**Performance Goals**: Review commands should read at most a few small local files and return immediately

**Constraints**: No new dependencies; no execution of proposed skills; preserve existing approval ledger semantics

**Scale/Scope**: One skill review at a time; no dashboard or global candidate index

## Constitution Check

- **Minimal, targeted changes**: Pass. Changes are confined to skill reporting helpers, registry accessors, agent command handlers, tests, and docs.
- **Provider-agnostic core**: Pass. No provider behavior changes.
- **Tool, skill, and playbook separation**: Pass. Review reads files and does not execute skills or tools.
- **Test coverage**: Pass. Add focused CLI command and approval-message tests.
- **Incremental philosophy**: Pass. Plain text review command is sufficient for this closeout issue.

## Project Structure

### Documentation (this feature)

```text
specs/017-lifecycle-cli-review/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── skill-review-command.md
└── tasks.md
```

### Source Code

```text
py_mono/
├── agent/
│   └── agent.py
└── skill/
    ├── base.py
    ├── diffing.py
    └── reporting.py

tests/
├── test_special_commands.py
└── test_generate_skill.py
```

**Structure Decision**: Keep report parsing/rendering in `py_mono/skill/reporting.py` and command routing in `py_mono/agent/agent.py`.

## Complexity Tracking

No constitution violations.
