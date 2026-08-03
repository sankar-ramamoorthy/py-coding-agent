---

description: "Task list for dual Ollama backend selection implementation"
---

# Tasks: Dual Ollama Backend Selection (Local + Remote GPU)

**Input**: Design documents from `/specs/002-ollama-dual-backend/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/provider-selection.md, quickstart.md

**Tests**: Included — Constitution Principle IV requires test coverage for new behavior.

**Organization**: Tasks are grouped by user story (US1/US2/US3 from spec.md).

## Path Conventions

All paths relative to the repository root. `py_mono/llm/` and `py_mono/config.py` are
existing files being modified; `tests/llm/` and `tests/session/` are new top-level test
directories (neither exists yet, confirmed by checking directly).

---

## Phase 1: Setup

- [ ] T001 Create `tests/llm/` and `tests/session/` directories

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: `base_url`-parameterized `OllamaProvider` plus explicit local/remote registry
resolution — needed by all three user stories (US1's auto-fallback delegates to the same
local/remote resolution; US2 IS this resolution exposed explicitly; US3's model override is
part of the same resolution logic).

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T002 Add optional `base_url: Optional[str] = None` constructor parameter to
      `OllamaProvider.__init__` in `py_mono/llm/ollama_provider.py` — falls back to
      `os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")` when omitted, so
      bare `ollama`'s behavior is byte-for-byte unchanged
- [ ] T003 [P] Write `tests/llm/test_ollama_provider.py`: explicit `base_url` argument wins
      over the env var; omitting it falls back to `OLLAMA_BASE_URL` exactly as before
      (backward-compatibility regression test for bare `ollama`)
- [ ] T004 Add `ollama-remote` and `ollama-local` entries to `REGISTRY` plus a
      `_OLLAMA_BACKENDS` dispatch table (backend name → base_url env/default, model
      env/default) and the resolution branch in `get_provider` in
      `py_mono/llm/provider_registry.py`, per `data-model.md`'s concrete table (depends on T002)
- [ ] T005 [P] Write `tests/llm/test_provider_registry.py` covering: `get_provider("ollama-remote")`
      resolves `OLLAMA_REMOTE_URL`/`OLLAMA_REMOTE_MODEL` defaults; `get_provider("ollama-local")`
      resolves `OLLAMA_LOCAL_URL`/`OLLAMA_LOCAL_MODEL` defaults; explicit `model` argument
      overrides the env default for either; bare `get_provider("ollama")` is unchanged
      (still only reads `OLLAMA_BASE_URL`/`OLLAMA_MODEL`); unknown name still raises
      `ValueError` listing all registry keys (depends on T004)

**Checkpoint**: Explicit local/remote resolution works — user story implementation can begin

---

## Phase 3: User Story 1 - Fast inference by default, with automatic fallback (Priority: P1) 🎯 MVP

**Goal**: A session with no explicit backend chosen automatically uses the remote backend
when reachable, and transparently falls back to local when it isn't.

**Independent Test**: Start a session with remote reachable (confirms remote is selected);
start a session with remote deliberately unreachable (confirms local is selected instead,
automatically).

### Tests for User Story 1 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T008, T009 don't exist yet)

- [ ] T006 [P] [US1] Write `tests/llm/test_ollama_connectivity.py`: `is_ollama_reachable`
      returns `True` on a mocked 2xx response; returns `False` on a mocked
      `requests.RequestException` (timeout, connection error) and on a mocked non-2xx response
- [ ] T007 [US1] Add `ollama-auto` test cases to `tests/llm/test_provider_registry.py`: mock
      `is_ollama_reachable` to return `True` → `get_provider("ollama-auto")` resolves via the
      `ollama-remote` path; mock it to return `False` → resolves via the `ollama-local` path.
      No real network calls in either case.

### Implementation for User Story 1

- [ ] T008 [US1] Create `py_mono/llm/ollama_connectivity.py` with
      `is_ollama_reachable(base_url: str, timeout: float = 2.0) -> bool` per `data-model.md`
- [ ] T009 [US1] Add `ollama-auto` to `REGISTRY` and its resolution branch in
      `py_mono/llm/provider_registry.py`: probe the remote backend's URL once via
      `is_ollama_reachable`, resolve to the `ollama-remote` construction path if reachable,
      else the `ollama-local` path (depends on T004, T008)
- [ ] T010 [US1] Change `LLM_PROVIDER`'s default from `"ollama"` to `"ollama-auto"` in
      `py_mono/config.py`; add doc-comment lines for the four new env vars
- [ ] T011 [US1] Update `.env.example`: `LLM_PROVIDER=ollama-auto`, add commented-out
      `OLLAMA_REMOTE_URL`, `OLLAMA_REMOTE_MODEL`, `OLLAMA_LOCAL_URL`, `OLLAMA_LOCAL_MODEL`
      lines showing their defaults
- [ ] T012 [US1] Update `docker-compose.yml`'s `py-coding-agent` service: add the four new
      env vars using the `${VAR:-default}` pattern; normalize `OLLAMA_BASE_URL` to the same
      pattern (small adjacent fix)
- [ ] T013 [US1] Run `pytest tests/llm/ -v` and confirm all foundational + US1 test cases
      (T003, T005, T006, T007) pass

**Checkpoint**: User Story 1 is fully functional and independently testable — remote-first
default with automatic fallback works (SC-001, SC-002).

---

## Phase 4: User Story 2 - Explicit backend override (Priority: P2)

**Goal**: A user can force either backend directly, bypassing the automatic default, with
unreachable explicit selections failing loudly rather than silently falling back.

**Independent Test**: Explicitly select remote and confirm it's used even when local would
otherwise have been auto-selected, and vice versa; explicitly select an unreachable backend
and confirm a direct error, not a silent fallback.

### Tests for User Story 2 ⚠️

- [ ] T014 [US2] Write `tests/session/test_session_manager.py`: `SessionManager`
      construction with `default_provider="ollama-remote"` and `default_provider="ollama-local"`
      each resolve to the correct backend (mock the underlying HTTP layer, no real network);
      `switch_provider("ollama-local", model=...)` updates `provider_name`/`provider` correctly

### Implementation for User Story 2

- [ ] T015 [US2] No new production code expected — `ollama-remote`/`ollama-local` explicit
      selection is already fully delivered by the Foundational phase (T004) and the existing
      `/provider <name> <model>` command (confirmed by reading `agent.py` during planning,
      zero changes needed there). This task is verification: confirm `get_provider` never
      calls `is_ollama_reachable` for these two names (i.e. explicit selections never probe
      or silently fall back) — add an assertion/test for this if not already covered by T005
- [ ] T016 [US2] Run `pytest tests/session/ -v` and confirm T014 passes

**Checkpoint**: User Stories 1 AND 2 both work independently — explicit override with loud
failure on unreachable selections (SC-003, FR-004).

---

## Phase 5: User Story 3 - Switch the model on either backend at runtime (Priority: P3)

**Goal**: A user can change which model a backend uses in one action, without a code change
or redeploy, and the override doesn't persist as a new default.

**Independent Test**: Select a backend together with a specific model, confirm that model is
used; select the same backend again without a model, confirm it reverts to the configured default.

### Tests for User Story 3 ⚠️

- [ ] T017 [US3] Add model-override test cases to `tests/llm/test_provider_registry.py` (if
      not already fully covered by T005): `get_provider("ollama-remote", model="qwen3:4b")`
      returns a provider configured with `qwen3:4b`, not the `OLLAMA_REMOTE_MODEL` default;
      a subsequent `get_provider("ollama-remote")` with no model argument reverts to the
      configured default (proves the override doesn't persist)

### Implementation for User Story 3

- [ ] T018 [US3] No new production code expected — model override is already delivered by
      the Foundational phase's `_OLLAMA_BACKENDS` resolution logic (T004: `model or
      os.getenv(...)`) and the existing `/provider <name> <model>` command. This task is
      verification only.
- [ ] T019 [US3] Run `pytest tests/llm/test_provider_registry.py -v` and confirm T017 passes

**Checkpoint**: All three user stories are independently functional (SC-001 through SC-006).

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T020 [P] Run `python -m compileall -q py_mono` — repo-wide syntax gate
- [ ] T021 Run `pytest` (full suite) at the repo root — confirm nothing existing regressed
- [ ] T022 Manually execute quickstart.md Scenarios 1–6 against the real backends (remote
      preferred by default, automatic fallback, explicit override, unreachable-explicit
      fails loudly, model override reverts after one use, `LLM_PROVIDER=ollama` backward
      compatibility) and confirm each behaves exactly as documented
- [ ] T023 Update `docs/ISSUES.md` (mark `ISS-007` done), and fill in
      `docs/SESSION_LOG.md`, `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md` with the real
      end-of-session state per AGENTS.md's Session Completion section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004, for `ollama-remote`/
  `ollama-local` to delegate to)
- **User Story 2 (Phase 4)**: Depends on Foundational only (T002, T004) — independent of US1
- **User Story 3 (Phase 5)**: Depends on Foundational only (T004's model-override logic) —
  independent of US1/US2
- **Polish (Phase 6)**: Depends on all three user stories being complete

### Parallel Opportunities

- T003 can run in parallel with T004 (different files: test file vs. registry, though T004
  should land first for T003's assertions to have something real to check against — treat
  as sequential in practice despite the [P] marker reflecting "different files")
- T005, T006 can run in parallel (different test files)
- Once Foundational (Phase 2) is done, US2 (Phase 4) and US3 (Phase 5) implementation tasks
  (T015, T018 — both "verification only") can proceed in parallel with US1's Phase 3, since
  neither depends on `ollama-auto`/the connectivity probe existing

---

## Parallel Example: after Foundational completes

```bash
# US1, US2, US3 test-writing can start together once T004 lands:
Task: "Write tests/llm/test_ollama_connectivity.py"          # US1
Task: "Write tests/session/test_session_manager.py"           # US2
Task: "Add model-override test cases to test_provider_registry.py"  # US3
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (`base_url` param + explicit local/remote resolution)
3. Complete Phase 3: User Story 1 — remote-preferred-by-default with fallback is live
4. **STOP and VALIDATE**: run quickstart.md Scenarios 1 and 2 for real
5. This alone already delivers the feature's core value (fast by default, no manual step)

### Incremental Delivery

1. Setup + Foundational → explicit local/remote resolution ready
2. Add User Story 1 → remote-first default + fallback (MVP)
3. Add User Story 2 → explicit override, loud failure on unreachable explicit selection
4. Add User Story 3 → model-override verification
5. Polish → repo-wide regression checks + real end-to-end quickstart proof

---

## Notes

- [P] tasks touch different files with no dependency on an incomplete task
- Tests (T003, T005, T006, T007, T014, T017) are written alongside or just before their
  corresponding implementation, per Constitution Principle IV
- US2 and US3's "implementation" tasks (T015, T018) are deliberately verification-only —
  the Foundational phase already delivers their behavior; this is expected given how much
  of this feature's value comes from extending an existing, already-general mechanism
  (`get_provider`/`REGISTRY`) rather than building new per-story machinery
- Commit after each phase completes (see plan.md's file-level change list for the natural
  commit boundary between Foundational+US1 vs. US2/US3 verification vs. Polish)
