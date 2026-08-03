# py-coding-agent Constitution

This constitution mirrors the "Agent Operating Constraints", "Protected Areas", and "Change
Philosophy" sections of AGENTS.md, which remains the canonical, human-facing contributor doc.
This file exists so Spec Kit's `/speckit-plan` and `/speckit-tasks` steps can consult the same
rules programmatically. If either document changes, update both in the same change.

## Core Principles

### I. Minimal, Targeted Changes
Prefer minimal, targeted changes over broad refactors. Do not restructure directories or
modules unless explicitly requested. Preserve existing patterns in `py_mono/` unless a change
is clearly scoped. Do not introduce new frameworks or major dependencies without approval.

### II. Provider-Agnostic Core
Preserve the provider-agnostic design in `py_mono/agent/`; keep provider-specific logic inside
the LLM provider and session layers only.

### III. Tool, Skill, and Playbook Separation
Use the `Tool.run(**kwargs)` interface for tool execution; never call underlying tool functions
directly. Keep playbooks in the reasoning layer only — execution logic belongs in tools and
approved skills. Do not introduce direct side effects outside the approved tool and skill paths.

### IV. Test Coverage for New Behavior
`pytest` is the expected test runner. New tests live under a top-level `tests/` package
mirroring the source layout (e.g. `tests/tools/test_shell.py`), named `test_*.py`. Cover new
tool behavior, provider branching, and sandbox-path edge cases before merging.

### V. Incremental Change Philosophy
Favor incremental improvements over large redesigns. Avoid breaking existing interfaces unless
explicitly requested. When proposing changes, briefly explain intent and impact, and verify
behavior against existing code and docs before changing it. When unsure, ask for clarification
before making large changes.

## Additional Constraints (Protected Areas)

- Do not modify `py_coding_agent.egg-info/`.
- Treat `docs/` and `docs/adr/` as reference unless explicitly editing documentation.
- Treat `workspace/` as the only safe sandbox area for generated files, not a source of truth.
- Be cautious modifying `skills/` — some entries are experimental or incomplete.
- Avoid hand-editing `dynamic_tools/` unless the task explicitly targets generated tools.
- Respect the `/workspace` boundary for file and shell effects; do not add flows that bypass
  sandbox path checks.
- Do not commit live secrets. Start from `.env.example`, keep API keys in environment
  variables, and use `LLM_MASTER_KEY` for encrypted key storage support.
- Do not enable execution of `proposed` or `deprecated` skills as part of routine feature work.

## Development Workflow

- Docker-first, `uv`-based workflow: `uv lock` after dependency changes, `docker compose build`
  to rebuild images, `docker compose run --rm py-coding-agent` for the interactive CLI,
  `python -m py_mono.main` as the simplest direct local entry point outside Docker.
- Commits: short, imperative messages, one concern per commit.
- PRs: summarize behavior changes, list affected areas, link any issue or ADR, and include
  terminal output or screenshots when CLI behavior changes.
- Spec Kit's `specs/<NNN>-<slug>/` artifacts are for planning and building an individual
  feature. Standing architecture decisions that outlive a single feature still go in
  `docs/adr/` as freeform `## Status/Context/Decision/Consequences` Markdown — Spec Kit does
  not replace that practice.

## Governance

This constitution supersedes ad-hoc practice for anything it and AGENTS.md both cover; where
the two differ, treat it as a bug and reconcile them in the same change. Amendments to either
document should be reflected in the other when they affect the same rule. `/speckit-plan` and
`/speckit-tasks` outputs must be checked against these principles before implementation begins.

**Version**: 1.0.0 | **Ratified**: 2026-08-03 | **Last Amended**: 2026-08-03
