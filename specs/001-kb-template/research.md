# Phase 0 Research: kb-template

No `NEEDS CLARIFICATION` markers remained in the Technical Context — the feature's own
description and the prior planning session already pinned down the technical choices below.
This file records the decisions and rejected alternatives for the record, per Spec Kit's
Phase 0 convention.

## Decision: Validator language and dependency

**Decision**: Python 3.10+, PyYAML only, packaged inside `kb-template/validator/` with its
own `pyproject.toml`.

**Rationale**: This repo is already Python/`uv`-based, so Python is the path of least
friction for anyone extending or running the validator from inside this repo. PyYAML is
already imported three times elsewhere in this repo's `py_mono/` tree (`skill/validator.py`,
`skill/base.py`, `playbook/playbookregistry.py`), just never declared explicitly — adding it
to kb-template's own `pyproject.toml` (and, additively, to this repo's root one) costs
nothing new in practice. Giving `kb-template/` its own `pyproject.toml` — rather than relying
on this repo's environment — is what actually satisfies the "extractable via `cp -r` /
`git subtree split` without untangling" requirement from the spec: a validator that only
runs inside py-coding-agent's `uv` environment isn't truly portable once copied elsewhere.

**Alternatives considered**:
- *No validator dependency at all (stdlib only, hand-rolled YAML-subset parser)* — rejected:
  front matter is real YAML (lists, nested structures for `related`), and reimplementing a
  parser to avoid one small, ubiquitous dependency is needless risk for no real portability
  gain (pyyaml has no native-code build requirements that would complicate copying).
- *Node.js/JS validator* — rejected: no JS tooling exists anywhere in this repo; would add a
  second language stack for a documentation-tooling feature with no other JS need.
- *Shell script validator* — rejected: YAML parsing and wikilink-graph resolution in POSIX
  shell would be fragile and non-portable across the Windows/Linux boundary this repo already
  straddles (Docker + native Windows dev, per ADR-007).

## Decision: Validator invocation shape

**Decision**: `uv run` from within `kb-template/` (`uv run --project kb-template python -m
validator.validate .` from the repo root, or `uv run python -m validator.validate .` from
inside `kb-template/` once copied elsewhere), single positional `root` argument defaulting to
the script's own parent directory.

**Rationale**: Matches this repo's stated Docker/`uv`-first workflow (AGENTS.md "Build, Test,
and Development Commands") while still working once `kb-template/` is copied to a location
with no relation to py-coding-agent — the default-to-own-parent-dir behavior means a bare
`uv run python -m validator.validate` works with no arguments needed in the common case.

**Alternatives considered**:
- *Always require an explicit path argument* — rejected: adds friction for the common
  case (validating the scaffold you're standing inside), with no real benefit.
- *A `pre-commit` hook shipped by default* — rejected: explicitly out of scope per the spec
  (wiring into any repo's CI/pre-commit is deferred); shipping one anyway would be
  unrequested scope.

## Decision: Wikilink syntax and resolution

**Decision**: In-body `[[target]]` (optionally `[[target|alias]]` or `[[target#section]]`),
resolved by filename stem, case-insensitively with a warning on case mismatch. The `related`
front-matter field holds plain document names (not bracketed strings).

**Rationale**: `[[target]]` is the de facto convention from Obsidian-style wikilinking that
the spec explicitly calls for, without requiring an actual Obsidian dependency (it's just a
text pattern). Filename-stem matching keeps authoring low-friction — writers don't need to
know a document's full relative path to link to it. Keeping `related:` as plain names avoids
awkward YAML-list-of-bracketed-strings syntax, reserving `[[...]]` for prose only.

**Alternatives considered**:
- *Full relative-path wikilinks* — rejected: more precise, but defeats the low-friction
  authoring goal that makes wikilinks worth using in the first place.
- *Case-sensitive-only matching* — rejected: too strict for a documentation tool where
  authors won't always remember exact casing; a warning is a better trade-off than a hard
  failure, while still catching genuine typos as separate broken-link errors when there is
  no matching stem at all under any case.

## Decision: Test location

**Decision**: `tests/kb_template/test_validate.py` at this repo's top level, not inside
`kb-template/` itself.

**Rationale**: Constitution Principle IV requires new tests under this repo's top-level
`tests/` package mirroring source layout. A test suite is also not something that needs to
travel with `kb-template/` when it's copied to another project — the *validator* is
portable; the proof that it works in *this* repo is this repo's own concern.

**Alternatives considered**:
- *Tests inside `kb-template/tests/`* — rejected: would violate Constitution Principle IV's
  explicit top-level `tests/` convention, and would need to be stripped out again if/when
  `kb-template/` is later extracted to its own repo (adding churn for no benefit, since a
  future standalone `kb-template` repo would define its own test setup at that time anyway).
