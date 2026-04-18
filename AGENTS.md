# Repository Guidelines

## Project Structure & Module Organization
Core application code lives in `py_mono/`. Key areas include `agent/` for the execution loop, `llm/` for provider integrations, `tools/` for built-in tools, `skill/` for the skills framework, `session/` for runtime provider state, and `ui/` for the CLI. Repo-level `skills/` contains individual skill packages (`SKILL.md` plus optional `skill.py`). `mcp_servers/datetime/` holds the sample FastMCP service. Use `dynamic_tools/` for runtime-generated tools, `workspace/` for sandboxed working files, and `docs/` plus `docs/adr/` for design notes and ADRs.

## Build, Test, and Development Commands
Use `uv` and Docker Compose for the standard workflow.

- `uv lock` updates the root lockfile after dependency changes.
- `docker compose build` rebuilds the agent and MCP images.
- `docker compose run --rm py-coding-agent` starts the interactive agent CLI.
- `docker compose run --rm py-coding-agent uv lock` refreshes locks in the Linux container workflow described in ADR-007.
- `python -m py_mono.main` is the simplest direct local entry point when running outside Docker.
- `pytest` runs the test suite once tests are present.

## Coding Style & Naming Conventions
Follow existing Python style: 4-space indentation, snake_case for functions/modules, PascalCase for classes, and concise docstrings on non-trivial functions. Keep modules focused and prefer small tool and skill entry points over large mixed-responsibility files. Continue the current naming patterns such as `*_tool.py`, `*_provider.py`, and skill directories like `skills/bug_fix/`.

## Testing Guidelines
`pytest` is the expected test runner, and several skills already invoke it. Add new tests under a top-level `tests/` package mirroring the source layout when possible, for example `tests/tools/test_shell.py`. Name files `test_*.py`, keep fixtures explicit, and cover new tool behavior, provider branching, and sandbox-path edge cases before merging.

## Commit & Pull Request Guidelines
Recent history uses short, imperative commit messages such as `added playbook` and `fixed issue with generate-skill`. Keep commits focused and descriptive; prefer one concern per commit. PRs should summarize behavior changes, list affected areas, link any issue or ADR, and include terminal output or screenshots when CLI behavior changes.

## Security & Configuration Tips
Do not commit live secrets. Start from `.env.example`, keep API keys in environment variables, and use `LLM_MASTER_KEY` for encrypted key storage support. Treat `workspace/` as the only safe execution area for generated files.

## Agent Operating Constraints
- Prefer minimal, targeted changes over broad refactors.
- Do not restructure directories or modules unless explicitly requested.
- Do not introduce new frameworks or major dependencies without approval.
- Preserve existing patterns in `py_mono/` unless a change is clearly scoped.
- When unsure, ask for clarification before making large changes.
- Keep edits aligned with the repository's Docker-first, sandboxed workflow.
- Verify behavior against existing code and docs before changing it.
- Preserve the provider-agnostic design in `py_mono/agent/`; keep provider-specific logic inside the LLM provider and session layers.
- Use the `Tool.run(**kwargs)` interface for tool execution; do not call underlying tool functions directly.
- Keep playbooks in the reasoning layer only; execution logic belongs in tools and approved skills.
- Do not introduce direct side effects outside the approved tool and skill paths.

## Protected Areas
- Do not modify `py_coding_agent.egg-info/`.
- Treat `docs/` and `docs/adr/` as reference unless explicitly editing documentation.
- Treat `workspace/` as a sandbox area, not a source of truth.
- Be cautious when modifying `skills/` because some entries are experimental or incomplete.
- Avoid hand-editing `dynamic_tools/` unless the task explicitly targets generated tools.
- Respect the `/workspace` boundary for file and shell effects; do not add flows that bypass sandbox path checks.

## Change Philosophy
This project is under active development with evolving architecture.

- Favor incremental improvements over large redesigns.
- Avoid breaking existing interfaces unless explicitly requested.
- When making changes, briefly explain intent and impact.
- Align changes with the modular, service-oriented structure of the codebase.
- Prefer fixes that preserve current CLI commands, provider wiring, and sandbox boundaries.
- Preserve the separation between playbooks for reasoning, orchestration for selection, and tools or skills for execution.
- Do not enable execution of `proposed` or `deprecated` skills as part of routine feature work.

## Interaction Style
- Provide concise, technical explanations.
- When proposing changes, include reasoning.
- Highlight trade-offs when relevant.
- Use concrete paths, commands, and examples when they help contributors act quickly.
