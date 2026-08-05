# Feature Specification: Minimal CI (pytest + compileall on every PR)

**Feature Branch**: `add-minimal-ci`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work)

**Input**: User description: "Add minimal CI per Milestone 6 — run pytest and
python -m compileall on every PR, since there is currently no CI or pre-commit enforcement
anywhere in this repo and every regression check has been a human manually running pytest.
Depends on ISS-005 landing first so the suite has no known-red tests to gate on. See
docs/ROADMAP_PLAN.md Milestone 6 and docs/ISSUES.md ISS-012."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Every PR gets an automated, visible pass/fail signal (Priority: P1)

A contributor (human or AI) opens a pull request. Instead of every regression check being a
human manually running `pytest` locally, the PR itself shows whether the full test suite and a
compile-check pass, automatically.

**Why this priority**: This is the concrete gap named in Milestone 6's "why first" reasoning —
there is currently zero automated enforcement in this repo.

**Independent Test**: Open a PR and confirm a CI run appears and reports pass/fail without any
manual step.

**Acceptance Scenarios**:

1. **Given** a pull request is opened against this repository, **When** CI runs, **Then** it
   installs this project's declared dependencies, runs the full `pytest` suite, and runs
   `python -m compileall` against `py_mono` and `skills`.
2. **Given** the full test suite passes locally, **When** the same commit runs in CI, **Then**
   CI also passes (no environment-specific drift between local and CI runs for the same code).
3. **Given** a push lands on `main` (e.g. after a PR merges), **When** CI runs, **Then** the same
   checks run against `main`'s new state.

### Edge Cases

- What if a PR predates `ISS-005`'s fix landing on `main`? CI will correctly show red for the 5
  pre-existing failures `ISS-005` fixes — this is accurate, not a CI bug, and is exactly why
  `ISS-005` was sequenced before this item in Milestone 6's scope.
- Does this make CI *required* (blocking merge on failure)? No — that's a separate GitHub branch
  protection setting change, out of scope for this item, which only adds the workflow itself
  (see Assumptions).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: CI MUST run automatically on every pull request, with no manual trigger required.
- **FR-002**: CI MUST run the full `pytest` suite.
- **FR-003**: CI MUST run `python -m compileall` against `py_mono` and `skills`.
- **FR-004**: CI MUST install dependencies using this project's existing dependency manager
  (`uv`), consistent with `AGENTS.md`'s documented `uv`-based workflow.
- **FR-005**: CI MUST also run on pushes to `main`, so a merge's resulting state is checked too.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A CI run appears on every new PR without any manual step.
- **SC-002**: CI's pass/fail outcome matches a local `pytest` + `compileall` run for the same
  commit (verified by running the exact CI commands locally before merging this change).
- **SC-003**: Once `ISS-005` (already fixed, pending merge) lands on `main`, CI shows green for
  the full suite with no known, undiagnosed red tests.

## Assumptions

- This item adds the CI *workflow* only. Making CI's result *required* to merge (branch
  protection requiring the status check) is a separate GitHub repository-settings change with
  repo-wide effect, and is intentionally left to the repository owner to enable explicitly
  rather than being toggled as part of this change.
- GitHub Actions (already the host for this repository) is used rather than introducing a new
  CI provider — no new external service dependency.
