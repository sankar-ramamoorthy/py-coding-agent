---

description: "Task list for fixing the Ollama thinking-model empty response bug"
---

# Tasks: Fix Ollama thinking-model empty response

**Input**: Design documents from `/specs/005-fix-ollama-thinking-response/`

**Prerequisites**: plan.md, spec.md, research.md, contracts/ollama-chat-request-contract.md

**Tests**: Included — FR-006 explicitly requires test coverage, and constitution Principle IV
requires it for new behavior.

**Organization**: This feature is a small, single-file fix (`py_mono/llm/ollama_provider.py` +
one config addition), so all three user stories touch the same `generate()` method. They're
still separated below by story for traceability, but tasks within the same file that edit the
same function are sequential, not parallel, even when grouped under different stories.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files/functions, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

## Path Conventions

Single project — `py_mono/`, `tests/` at repository root (existing layout, no new
directories).

---

## Phase 1: Setup

**Purpose**: Add the new configuration values every story depends on.

- [x] T001 Add `OLLAMA_ENABLE_THINKING` (default `false`), `OLLAMA_NUM_PREDICT` (default
      `4096`), `OLLAMA_NUM_CTX` (default `8192`), and `OLLAMA_REQUEST_TIMEOUT` (default `600`,
      replacing the prior hardcoded `300`) to `py_mono/config.py`, following the existing
      `os.getenv(...)`-with-default pattern used for `OLLAMA_MODEL`/`OLLAMA_BASE_URL` and
      `ENABLE_SHELL_TOOL`. Document all four in the module's env-var docstring block (see
      `research.md` for chosen defaults and rationale). **Revised during implementation**: the
      original task only planned two config values; `OLLAMA_ENABLE_THINKING` and
      `OLLAMA_REQUEST_TIMEOUT` were added after empirical testing (see `research.md`) showed
      `think: false` is the actually-effective primary fix for the model that produced the bug
      report, and that the prior hardcoded 300s timeout is insufficient for the budget-only
      fallback path.

**Checkpoint**: Config values exist and are importable — no behavior change yet.

---

## Phase 2: Foundational

No additional blocking work beyond Phase 1 — the config values in T001 are the only shared
prerequisite. Proceed directly to User Story 1.

---

## Phase 3: User Story 1 - Thinking-capable model returns usable output (Priority: P1) 🎯 MVP

**Goal**: A thinking-capable local model no longer returns an empty response by exhausting its
budget on internal reasoning before producing real content.

**Independent Test**: Per `quickstart.md` Scenario 1 (reproduce pre-fix baseline) and Scenario 2
(confirm fix via `/skill generate_skill`) — a prompt that previously produced empty `content`
with `done_reason: "length"` now returns usable content.

### Tests for User Story 1

> Write these first; confirm they fail against the current (unfixed) `generate()`.

- [x] T002 [P] [US1] Add `test_generate_sends_num_predict_and_num_ctx` to
      `tests/llm/test_ollama_provider.py` — mock `requests.post`, call `generate()`, assert the
      posted JSON payload includes `options.num_predict` and `options.num_ctx` matching the
      configured values.
- [x] T003 [P] [US1] Add `test_generate_unaffected_for_non_thinking_model_payload` to
      `tests/llm/test_ollama_provider.py` — same assertion as T002 but confirms the payload
      shape doesn't special-case any particular model name (FR-002: no behavior branching on
      "is this a thinking model", since the provider can't reliably know that in advance).

### Implementation for User Story 1

- [x] T004 [US1] In `py_mono/llm/ollama_provider.py`, import the new config values and add
      `"options": {"num_predict": OLLAMA_NUM_PREDICT, "num_ctx": OLLAMA_NUM_CTX}` plus, by
      default, `"think": False` to the payload built in `generate()` (depends on T001; must not
      remove or reorder existing payload keys). Also switch `requests.post(..., timeout=300)` to
      `timeout=OLLAMA_REQUEST_TIMEOUT`. **Revised during implementation**: `think: false` was
      added here (originally planned as absent per the pre-implementation research draft) after
      testing against the actual model from the bug report showed it, not budget alone, is the
      effective primary fix — see `research.md`.
- [x] T005 [US1] Run T002/T003 and confirm they now pass against the updated `generate()`.
      Additionally validated end-to-end against real Ollama servers (not just mocks) for both
      models this agent uses — see `research.md`'s "Final end-to-end confirmation."

**Checkpoint**: User Story 1 is independently functional — run `quickstart.md` Scenarios 1-3
against a real Ollama server to confirm end-to-end.

---

## Phase 4: User Story 2 - Future issues are diagnosable without re-deriving root cause (Priority: P2)

**Goal**: When a thinking-capable model's response includes a separate `thinking` field,
existing debug output surfaces it — so a future empty-`content` failure is diagnosable from logs
alone.

**Independent Test**: Per `quickstart.md` Scenario 4 — with `DEBUG` enabled and a tight budget
forcing truncation, the debug output shows the `thinking` field's content.

### Tests for User Story 2

- [x] T006 [P] [US2] Add `test_generate_logs_thinking_field_when_present` to
      `tests/llm/test_ollama_provider.py` — mock a response with a non-empty `message.thinking`
      and empty `message.content`; capture stdout/log output (matching this file's existing
      style for asserting on `DEBUG` prints) and assert the `thinking` text appears in it.
- [x] T007 [P] [US2] Add `test_generate_no_error_when_thinking_field_absent` to
      `tests/llm/test_ollama_provider.py` — mock a response with no `thinking` key at all
      (non-thinking model shape) and confirm `generate()` does not raise.

### Implementation for User Story 2

- [x] T008 [US2] No code change needed — the existing `DEBUG` block already dumps the entire
      raw response dict (`json.dumps(data, indent=2)`), which already includes `message.thinking`
      when present, with no `.get()` call needed and no risk of `KeyError` when absent. Confirmed
      by T006/T007 passing against the pre-fix code unchanged. Documented here rather than left
      unrecorded, since a plausible-looking task ("read and log the field") turned out to already
      be satisfied by existing behavior.
- [x] T009 [US2] Run T006/T007 and confirm they pass.

**Checkpoint**: User Stories 1 AND 2 both work — a truncation event is both less likely (US1)
and, if it still happens, diagnosable from logs (US2).

---

## Phase 5: User Story 3 - Reasoning can still be surfaced when genuinely wanted (Priority: P3)

**Goal**: An operator who wants a model to reason (rather than the default suppressed-thinking
behavior) can enable it, without losing the budget safety net.

**Independent Test**: Per `quickstart.md` — with `OLLAMA_ENABLE_THINKING=true`, the `think`
field is omitted from the request (not forced `true` — omission lets the model reason natively)
and `options.num_predict`/`num_ctx` are still present.

**Revised during implementation**: the original plan assumed no new implementation was needed
here, on the (later-corrected) premise that the fix would never send a `think` field at all. Once
`think: false` became the default (see US1's revision), US3 needed a real, tested escape hatch —
`OLLAMA_ENABLE_THINKING` — rather than being trivially satisfied by the absence of any `think`
handling.

### Tests for User Story 3

- [x] T010 [P] [US3] Add `test_generate_sends_think_false_by_default` to
      `tests/llm/test_ollama_provider.py` — mock `requests.post`, call `generate()`, assert the
      posted JSON payload has `"think": false`.
- [x] T010b [P] [US3] Add `test_generate_omits_think_when_thinking_explicitly_enabled` —
      with `OLLAMA_ENABLE_THINKING` patched `true`, assert no `"think"` key is sent and the
      `options` safety net is still present.

### Implementation for User Story 3

- [x] Covered by T004 (`if not OLLAMA_ENABLE_THINKING: payload["think"] = False`).

**Checkpoint**: All three user stories pass independently.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T010c [P] Add `test_generate_uses_configured_request_timeout` to
      `tests/llm/test_ollama_provider.py` — cross-cutting (not tied to one user story): confirms
      the previously-hardcoded `timeout=300` now reads from `OLLAMA_REQUEST_TIMEOUT`, discovered
      necessary when the budget safety net alone raised `ReadTimeout` in real testing.
- [x] T011 [P] Update the module docstring / inline comments in
      `py_mono/llm/ollama_provider.py` to note the new `think`/`options.num_predict`/`num_ctx`
      behavior and why (short pointer to
      `specs/005-fix-ollama-thinking-response/research.md`, not a full copy of the rationale).
- [x] T012 Run `pytest tests/llm/test_ollama_provider.py -v` and confirm all tests (existing +
      new) pass — 11/11 passed. Also ran the full suite (`pytest -q`); no regressions beyond the
      two pre-existing, already-tracked `ISS-005` failures.
- [x] T013 Ran the equivalent of `quickstart.md` Scenarios 1-2 directly against real Ollama
      servers during planning/implementation (both the local default model and the actual
      remote/`qwen3.5:4b` host) rather than only via the CLI — see `research.md`'s "Final
      end-to-end confirmation." Results recorded in `docs/SESSION_LOG.md`.
- [ ] T014 Update `docs/ISSUES.md` ISS-009 status from `open` to `done`, linking the merged
      commit(s) and this spec directory, per the existing entries' format (see ISS-002/ISS-003
      for the closed-entry style to match).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately.
- **Foundational (Phase 2)**: Empty — nothing beyond Phase 1 blocks the user stories.
- **User Story 1 (Phase 3)**: Depends on T001. This is the MVP — the concretely reported bug.
- **User Story 2 (Phase 4)**: Depends on T001. Independent of US1's payload change (different
  part of `generate()` — response parsing vs. request building) but conventionally implemented
  after US1 since both land in the same PR for a fix this small.
- **User Story 3 (Phase 5)**: Depends on T004/T008 already existing (it's a regression test over
  their absence of a `think` field, not new logic).
- **Polish (Phase 6)**: Depends on all three user stories being complete.

### Parallel Opportunities

- T002 and T003 can be written in parallel (different test functions, same file — fine to draft
  together, but committed as part of the same small change).
- T006 and T007 similarly.
- T004 and T008 are NOT parallel with each other — both edit `generate()` in the same file;
  do T004 (request side) before T008 (response side) to keep the diff easy to review in two
  clean steps rather than one large simultaneous edit.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 (T001).
2. Complete Phase 3 / US1 (T002-T005).
3. **STOP and VALIDATE**: Run `quickstart.md` Scenarios 1-3 against a real Ollama server. This
   alone resolves the reported bug (ISS-009).
4. Add US2 (T006-T009) and US3 (T010) — small enough that, in practice, all three land in one
   PR rather than separate incremental deploys, but the phase split keeps each story's tests and
   intent traceable per Spec Kit convention.
5. Complete Phase 6 (T011-T014) to close out documentation and the issue.

---

## Notes

- This feature has no data entities and no interface contract beyond the one documented in
  `contracts/ollama-chat-request-contract.md` — no `data-model.md` tasks needed beyond what's
  already covered.
- Every implementation task names the exact file it touches
  (`py_mono/config.py`, `py_mono/llm/ollama_provider.py`, `tests/llm/test_ollama_provider.py`) —
  no new files or directories beyond what already exists.
- Commit after each phase, not each task, given how small this feature is — T001 alone isn't a
  useful commit on its own.
