# Tasks: Minimal CI (pytest + compileall on every PR)

**Input**: Design documents from `/specs/010-add-minimal-ci/`

All tasks below were already executed and verified.

## Phase 1: Setup

- [x] T001 Confirm no `.github/workflows/` directory exists yet — zero CI currently configured

## Phase 2: User Story 1 - Every PR gets an automated pass/fail signal (Priority: P1)

- [x] T002 [US1] Create `.github/workflows/ci.yml`: trigger on `pull_request` and `push` to
      `main`, run on `ubuntu-latest`
- [x] T003 [US1] Use `astral-sh/setup-uv` to install `uv`, then `uv python install` and
      `uv sync --group dev`
- [x] T004 [US1] Add `uv run pytest -q` step
- [x] T005 [US1] Add `uv run python -m compileall -q py_mono skills` step
- [x] T006 [US1] Validate locally before relying on a live CI run: branched `add-minimal-ci`
      from `main` and merged in `fix-pre-existing-test-failures` (`ISS-005`) so this branch has
      no known-red tests, then ran the exact CI commands locally
      (`uv sync --group dev`, `uv run pytest -q`, `uv run python -m compileall -q py_mono
      skills`) — 104 passed, 1 skipped, compileall clean

## Dependencies & Execution Order

Single linear sequence. Depends on `ISS-005` (already fixed, `#96`) having landed for CI to
show green against `main`'s eventual state, per Milestone 6's documented ordering.
