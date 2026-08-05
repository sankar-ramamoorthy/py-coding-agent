# Implementation Plan: Fix Ollama thinking-model empty response

**Branch**: `fix-ollama-thinking-response` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-fix-ollama-thinking-response/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command; its definition describes the execution workflow.

## Summary

`OllamaProvider.generate()` sends Ollama chat requests with no `options.num_predict`/`num_ctx`
budget set. Empirically confirmed against the real local Ollama server (see `research.md`):
under a constrained response budget, a thinking-capable model (the agent's own **default**
model, `lfm2.5-thinking:latest`) returns `content: ""` with `done_reason: "length"` and a
separate, non-empty `message.thinking` field — the model spent its whole budget reasoning and
never reached the answer. A generous budget resolves it. This contradicts the chat-based
diagnosis's top recommendation (`think: false`, tested and confirmed *not* to suppress
reasoning for this model) — the fix is budget-based (Ollama's `options.num_predict`/`num_ctx`),
not a `think` toggle, plus surfacing the separate `thinking` field in debug output and in a more
actionable failure message.

## Technical Context

**Language/Version**: Python 3.11 (existing codebase, unchanged)

**Primary Dependencies**: `requests` (already used by `OllamaProvider`) — no new dependencies

**Storage**: N/A — no persisted state; this changes request/response handling only

**Testing**: `pytest`, mocking `requests.post` (existing pattern in `tests/llm/test_ollama_provider.py`) — no real Ollama server required for the test suite, though this plan's research was validated against a real local server

**Target Platform**: Same as existing agent runtime (Docker container / local Python entry
point) — not platform-specific

**Project Type**: Single project (existing agent codebase; no new project/package)

**Performance Goals**: No regression for non-thinking models or other providers; thinking-model
calls should complete without truncation for prompts of similar complexity to the one that
originally failed (`prompt_eval_count` ~451, needed `eval_count` >3645 to complete reasoning +
answer)

**Constraints**: Fix confined to the shared `OllamaProvider` request/response path
(`py_mono/llm/ollama_provider.py`) and its config (`py_mono/config.py`); no other provider
touched

**Scale/Scope**: Small — one provider file, one config addition, one test file update

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Minimal, Targeted Changes)**: PASS — single shared file
  (`py_mono/llm/ollama_provider.py`) plus one new config value, following the existing
  `ENABLE_SHELL_TOOL`/`ENABLE_DYNAMIC_TOOLS` env-var pattern. No restructuring.
- **Principle II (Provider-Agnostic Core)**: PASS — the fix lives entirely inside the Ollama
  provider layer; `py_mono/agent/` and other providers are untouched.
- **Principle III (Tool/Skill/Playbook Separation)**: N/A — no tool, skill, or playbook changes.
- **Principle IV (Test Coverage for New Behavior)**: PASS — new tests planned in the existing
  `tests/llm/test_ollama_provider.py`, mirroring its current mock-based style.
- **Principle V (Incremental Change Philosophy)**: PASS — `OllamaProvider.generate()`'s
  signature and behavior for non-thinking models are unchanged; the new config defaults to the
  fixed behavior (since the old behavior was a bug, not a feature anyone relies on), documented
  in `docs/adr/` is not required (this is a bug fix, not a standing architecture decision) but
  the change and rationale are recorded here and in `research.md`.

No violations. Complexity Tracking table not needed.

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: [Document the selected structure and reference the real
directories captured above]

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
