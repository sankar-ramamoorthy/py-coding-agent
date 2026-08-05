# Tasks: `generate_skill` output-quality fixes

**Input**: Design documents from `/specs/009-generate-skill-quality-issues/`

All tasks below were already executed and verified.

## Phase 1: Setup

- [x] T001 Re-confirm both code-level findings against current `main`: read
      `py_mono/skill/validator.py`'s `_strip_markdown_fences` and
      `py_mono/skill/prompts.py`'s `build_skill_md_prompt` to verify both bugs as filed are
      still present

## Phase 2: User Story 1 - Fenced output parses regardless of fencing shape (Priority: P1)

- [x] T002 [US1] Rewrite `_strip_markdown_fences` in `py_mono/skill/validator.py`: regex search
      (`` ```[lang]\n(.*?)``` ``, `re.DOTALL`) for a complete fenced block anywhere in the text;
      fall back to stripping a lone leading/trailing fence line if no complete pair is found
- [x] T003 [US1] [P] Add `tests/test_skill_validator.py` (7 tests): symmetric fence (regression),
      no-language-tag fence, leading-only fence, trailing-only fence (previously broken),
      preamble-before-fence (previously broken), no fence at all, multiline code preserved
- [x] T004 [US1] Run `pytest tests/test_skill_validator.py -v`: 7 passed

## Phase 3: User Story 2 - No leaked template instructions in generated SKILL.md (Priority: P1)

- [x] T005 [US2] Mark `build_skill_md_prompt()`'s three fillable sections (paragraph
      description, expected output, constraints) with explicit `[INSTRUCTION — ...]` prefixes in
      `py_mono/skill/prompts.py`
- [x] T006 [US2] Add a closing rule reinforcing that `[INSTRUCTION — ...]` lines must never be
      copied into the model's output
- [x] T007 [US2] [P] Add `tests/test_skill_prompts.py` (3 tests): old ambiguous line is gone,
      exactly 5 occurrences of the instruction marker (3 placeholders + 2 mentions in the
      closing rule), rule text present
- [x] T008 [US2] Run `pytest tests/test_skill_prompts.py -v`: 3 passed

## Phase 4: User Story 3 - Document the remote-backend GPU-offload question (Priority: P2)

- [x] T009 [US3] Confirm `OLLAMA_REMOTE_URL` (`http://100.105.24.12:11434`, from
      `.env.example`) is reachable from this session via `curl`
- [x] T010 [US3] Query `/api/generate` for `qwen2.5-coder:7b-instruct-q5_K_M` (the model from
      the original bug report) with a moderate-complexity prompt, then `/api/ps` immediately
      after: `size_vram: 0` against a `size` of ~5.8 GB
- [x] T011 [US3] [P] Repeat against a second, smaller model already loaded on the same host
      (`qwen3.5:4b`) to confirm the finding is host-wide, not model-specific: also
      `size_vram: 0`
- [x] T012 [US3] Record findings in `research.md`: the remote backend is not GPU-offloading any
      currently-tested model, explaining the originally-reported near-parity throughput; root
      cause of *why* GPU offload isn't happening flagged as needing direct host access, out of
      this session's reach

## Phase 5: Polish & Cross-Cutting

- [x] T013 Run full suite + `compileall`: no new regressions (5 pre-existing, unrelated
      `ISS-005` failures present, tracked/fixed separately in PR #96); 10 new tests included in
      the pass count

## Dependencies & Execution Order

User Stories 1, 2, and 3 are fully independent (different files, no shared state) and were
executed in parallel in practice.
