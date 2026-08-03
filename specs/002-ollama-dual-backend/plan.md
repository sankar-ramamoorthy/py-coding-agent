# Implementation Plan: Dual Ollama Backend Selection (Local + Remote GPU)

**Branch**: `ollama-dual-backend` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/002-ollama-dual-backend/spec.md`

## Summary

Add `ollama-remote`, `ollama-local`, and `ollama-auto` entries to
`py_mono/llm/provider_registry.py`'s `REGISTRY`, all instantiating the existing
`OllamaProvider` class (given a newly-added optional `base_url` constructor parameter) with
per-backend URL/model resolved from new env vars. `ollama-auto` performs a one-time,
short-timeout reachability probe (new `py_mono/llm/ollama_connectivity.py`) against the
remote backend and falls back to local if unreachable; it becomes the new
`LLM_PROVIDER` default. Bare `ollama` (and anyone with `LLM_PROVIDER=ollama` explicitly set)
keeps today's exact single-backend, non-probing behavior untouched. Runtime model switching
for the new explicit backends works immediately via the existing `/provider <name> <model>`
command — no command-dispatch changes required.

## Technical Context

**Language/Version**: Python 3.10+ (matches this repo's `requires-python`)

**Primary Dependencies**: `requests` (already a direct dependency) — no new dependencies

**Storage**: N/A — configuration via environment variables only

**Testing**: `pytest`, new tests at `tests/llm/` (new dir, mirrors `py_mono/llm/`) and
`tests/session/` (new dir), per Constitution Principle IV. All mocked — zero real network
calls in the automated suite.

**Target Platform**: Cross-platform (Docker container reaching a Windows/Linux host via
`host.docker.internal`, and a remote host over Tailscale)

**Project Type**: Backend/library change within an existing monolith (`py_mono/`), not a
new service

**Performance Goals**: The reachability probe (`ollama-auto` only) must add no perceptible
delay beyond a short, bounded timeout (2s) at selection time; zero added latency for
already-connected sessions or explicit `ollama-remote`/`ollama-local`/`ollama` selections

**Constraints**: Must not modify `py_mono/agent/agent.py`'s command-dispatch logic, the
shell tool, dynamic-tool loading, or the execution loop (per `ISS-002`/`ISS-003`); no new
dependencies; bare `ollama`'s behavior and default model must not change

**Scale/Scope**: Small, targeted change — one new small module, edits to two existing
provider files, one config default, and env/compose wiring

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Minimal, Targeted Changes** — PASS. No restructuring; `OllamaProvider` gains one
  optional constructor parameter, `provider_registry.py` gains new dict entries and a small
  resolution branch, `config.py` gains a changed default. No new frameworks/dependencies.
- **II. Provider-Agnostic Core** — PASS. Provider-specific logic (backend URLs, reachability
  probing) stays entirely inside `py_mono/llm/`; nothing in `py_mono/agent/` needs to know
  which Ollama backend is active.
- **III. Tool, Skill, and Playbook Separation** — N/A. No new tool, skill, or playbook;
  this is provider-layer configuration, not tool execution.
- **IV. Test Coverage for New Behavior** — PASS (planned). New tests at `tests/llm/` and
  `tests/session/`, top-level, mirroring source layout, `test_*.py` named.
- **V. Incremental Change Philosophy** — PASS. Purely additive for explicit selections;
  the one existing-behavior change (`LLM_PROVIDER`'s *default* value) is explicitly
  requested by the user and preserves exact backward compatibility for anyone with an
  existing `.env` setting `LLM_PROVIDER=ollama`.

No violations requiring justification. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-ollama-dual-backend/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── provider-selection.md   # Phase 1 output — /provider command + registry contract
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
py_mono/llm/
├── ollama_provider.py          # MODIFIED — add optional base_url constructor param
├── ollama_connectivity.py      # NEW — is_ollama_reachable(base_url, timeout=2.0)
└── provider_registry.py        # MODIFIED — new REGISTRY entries + _OLLAMA_BACKENDS + resolution

py_mono/config.py                # MODIFIED — LLM_PROVIDER default "ollama" -> "ollama-auto"
.env.example                     # MODIFIED — new env vars documented, new default shown
docker-compose.yml                # MODIFIED — new env vars wired with ${VAR:-default}

tests/llm/                        # NEW — mirrors py_mono/llm/
├── test_ollama_provider.py
├── test_provider_registry.py
└── test_ollama_connectivity.py

tests/session/                    # NEW — mirrors py_mono/session/
└── test_session_manager.py
```

**Structure Decision**: This is a targeted change within the existing `py_mono/llm/`
package — no new top-level structure needed. Tests land under this repo's existing
top-level `tests/` convention (mirroring `tests/tools/`, `tests/kb_template/`), in two new
subdirectories since neither `tests/llm/` nor `tests/session/` exist yet (confirmed by
checking directly).

## Complexity Tracking

*No violations — table not needed.*
