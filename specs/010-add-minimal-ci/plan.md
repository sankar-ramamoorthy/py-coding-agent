# Implementation Plan: Minimal CI (pytest + compileall on every PR)

**Branch**: `add-minimal-ci` | **Date**: 2026-08-05 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/010-add-minimal-ci/spec.md`

## Summary

Added `.github/workflows/ci.yml`: a GitHub Actions workflow triggered on `pull_request` and on
`push` to `main`, running on `ubuntu-latest`. Uses `astral-sh/setup-uv` to install `uv`
(matching this repo's existing dependency-manager convention), `uv sync --group dev` to install
dependencies including the `pytest` dev group, then `uv run pytest -q` and
`uv run python -m compileall -q py_mono skills`. Verified locally by running the exact same
commands (`uv sync --group dev`, `uv run pytest -q`, `uv run python -m compileall -q py_mono
skills`) against this branch, which already has `ISS-005`'s fix merged in — 104 passed, 1
skipped, compileall clean.

## Technical Context

**Language/Version**: N/A (CI configuration, not application code)

**Primary Dependencies**: `astral-sh/setup-uv` GitHub Action (installs `uv`, already this
project's dependency manager — no new dependency-management tooling introduced)

**Storage**: N/A

**Testing**: The CI workflow itself *is* the testing infrastructure being added; validated by
running its exact commands locally first

**Target Platform**: `ubuntu-latest` (GitHub-hosted runner) — chosen over matching the local
Windows dev environment because it's GitHub Actions' standard, zero-config runner and this
project's actual deployment target (Docker container) is Linux-based, not Windows

**Project Type**: Single project — one new workflow file

**Constraints**: Adds only the workflow; does not modify GitHub branch-protection settings (see
spec.md Assumptions) — that's a separate, repo-owner-only action

**Scale/Scope**: Minimal — one new YAML file

## Constitution Check

- **Principle I (Minimal, Targeted Changes)**: PASS — one new file, no existing files modified,
  no new application dependency (uses the existing `uv`/`pyproject.toml` setup as-is).
- **Principle IV (Test Coverage for New Behavior)**: N/A in the usual sense — this item *is* the
  test-coverage-enforcement infrastructure; validated by running its commands locally before
  merging (SC-002).
- **Principle V (Incremental Change Philosophy)**: PASS — purely additive; does not change how
  any existing command behaves locally.

No violations.

## Project Structure

### Source Code (repository root)

```text
.github/workflows/ci.yml   # new: pytest + compileall on every PR and on push to main
```

**Structure Decision**: `.github/workflows/` is GitHub Actions' standard, required location —
no alternative structure considered.
