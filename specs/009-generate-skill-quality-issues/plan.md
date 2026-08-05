# Implementation Plan: `generate_skill` output-quality fixes

**Branch**: `fix-generate-skill-quality-issues` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/009-generate-skill-quality-issues/spec.md`

## Summary

Two code fixes plus one non-code investigation, independent of each other. (1)
`_strip_markdown_fences` (`py_mono/skill/validator.py`) rewritten to find a fenced block via
regex anywhere in the text rather than requiring the string to start with one, fixing
trailing-only and preamble-prefixed fences. (2) `build_skill_md_prompt()`
(`py_mono/skill/prompts.py`) template sections marked with explicit `[INSTRUCTION — ...]`
prefixes plus a reinforcing closing rule, so the model can't mistake instructional prose for
literal content to echo back. (3) Confirmed via direct API queries against the remote Ollama
backend (`size_vram: 0` for two different loaded models) that it is not GPU-offloading
inference at all — documented in `research.md`, no code change applies.

## Technical Context

**Language/Version**: Python (unchanged)

**Primary Dependencies**: None new — `re` already imported in `validator.py`

**Storage**: N/A

**Testing**: `pytest`; new `tests/test_skill_validator.py` (7 tests) and
`tests/test_skill_prompts.py` (3 tests)

**Target Platform**: Unchanged for the code fixes; Finding 3's investigation used direct HTTP
access to the remote Ollama host's API (`http://100.105.24.12:11434`, reachable from this
session per `.env.example`'s documented `OLLAMA_REMOTE_URL`)

**Project Type**: Single project — two existing files changed

**Constraints**: Fixes confined to `py_mono/skill/validator.py`'s `_strip_markdown_fences` and
`py_mono/skill/prompts.py`'s `build_skill_md_prompt`; no other validator/prompt logic touched;
Finding 3 produces no code change by design (external server configuration, not this repo's
logic)

**Scale/Scope**: Small — one function rewritten, one prompt template's wording adjusted, two new
test files (10 tests total)

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS — `_strip_markdown_fences` keeps its
  existing signature and call sites unchanged; the prompt fix is a wording change to existing
  template sections, not new sections or new parameters.
- **Principle IV (Test Coverage for New Behavior)**: PASS — 10 new tests across two new test
  files covering both fixes' previously-uncovered behavior.
- **Principle V (Incremental Change Philosophy)**: PASS — the already-working symmetric-fence
  case is preserved (regression test included); the prompt's existing guidance prose is kept,
  only marked more explicitly rather than replaced.

No violations.

## Project Structure

### Source Code (repository root)

```text
py_mono/skill/validator.py        # _strip_markdown_fences rewritten (regex-based)
py_mono/skill/prompts.py          # build_skill_md_prompt(): [INSTRUCTION — ...] markers added
tests/test_skill_validator.py     # new: 7 tests
tests/test_skill_prompts.py       # new: 3 tests
```

**Structure Decision**: No new structure — two existing files changed, two new flat test files
(matches this repo's existing flat `tests/` convention).
