# Implementation Plan: kb-template — Portable Knowledge-Base Scaffold

**Branch**: `kb-template` | **Date**: 2026-08-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/001-kb-template/spec.md`

## Summary

Add a self-contained, top-level `kb-template/` directory to py-coding-agent: a canonical
YAML front-matter schema, a raw/processed/topics folder lifecycle with a navigation index,
an explicit promotion rule, one example document per type, and a standalone Python
validator (its own `pyproject.toml`, PyYAML only) that checks schema compliance, wikilink
resolution, and the promotion rule. The validator mirrors the existing front-matter-parsing
idiom in `py_mono/skill/validator.py` but has zero import dependency on this repo's runtime,
so `kb-template/` can be `cp -r`'d or `git subtree split` into a standalone repo later
without untangling.

## Technical Context

**Language/Version**: Python 3.10+ (matches this repo's `requires-python`)

**Primary Dependencies**: PyYAML only, declared in kb-template's own `pyproject.toml` (kept
independent of this repo's dependency set); this repo's root `pyproject.toml` also gets an
explicit `pyyaml` dependency added, since it's already used transitively by
`py_mono/skill/validator.py`, `py_mono/skill/base.py`, and `py_mono/playbook/playbookregistry.py`
without being declared

**Storage**: N/A — plain Markdown/YAML files on disk, no database

**Testing**: `pytest`, new tests at `tests/kb_template/test_validate.py` (top-level, mirrors
the existing `tests/tools/` convention), per Constitution Principle IV

**Target Platform**: Cross-platform CLI (runs anywhere `uv`/Python 3.10+ is available;
developed and verified on Windows in this repo)

**Project Type**: Portable documentation scaffold + accompanying validator CLI (not a
web/mobile app; closest existing precedent in this repo is a standalone tool package)

**Performance Goals**: N/A — validator runs over a small number of Markdown files (dozens,
not thousands); no performance target beyond "completes near-instantly for a typical KB"

**Constraints**: Must not import from or depend on `py_mono/` or any other runtime source in
this repo; must ship no project-specific canonical content; must remain plain Markdown/YAML
(no Obsidian-specific dependency); this repo has no ruff/mypy/CI configured today, so
verification relies on `python -m compileall` and `pytest` only

**Scale/Scope**: A handful of schema/index/example files plus one small validator package;
not expected to grow beyond low tens of files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Minimal, Targeted Changes** — PASS. `kb-template/` is a new, self-contained top-level
  directory; no existing `py_mono/` module is restructured. The one existing-file touch
  outside `kb-template/` is adding `pyyaml` to the root `pyproject.toml` dependency list —
  additive, not restructuring, and justified because it's already a live transitive
  dependency being made explicit, not a new capability.
- **II. Provider-Agnostic Core** — N/A. This feature does not touch `py_mono/agent/` or any
  LLM provider/session code.
- **III. Tool, Skill, and Playbook Separation** — N/A. This feature adds no new `Tool`,
  skill, or playbook; the validator is a standalone script, not part of this repo's tool
  execution path.
- **IV. Test Coverage for New Behavior** — PASS (planned). New tests land at
  `tests/kb_template/test_validate.py`, top-level, mirroring source layout, `test_*.py`
  named, per the constitution's own wording.
- **V. Incremental Change Philosophy** — PASS. Additive only; no existing interface changes.

No violations requiring justification. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/001-kb-template/
├── plan.md              # This file
├── research.md           # Phase 0 output
├── data-model.md         # Phase 1 output
├── quickstart.md         # Phase 1 output
├── contracts/
│   └── validator-cli.md  # Phase 1 output — validator's CLI contract
└── tasks.md              # Phase 2 output (/speckit-tasks — not created here)
```

### Source Code (repository root)

```text
kb-template/                              # NEW — self-contained, portable scaffold
├── README.md                             # what this is, how to copy it, quickstart
├── pyproject.toml                        # declares pyyaml only — standalone runnable
├── docs/
│   ├── schema.md                         # canonical front-matter schema
│   ├── authoring-rules.md                # canonical-doc rules + raw-note rules
│   └── promotion.md                      # promotion rule (status flip + physical move)
├── knowledge/
│   ├── raw/README.md
│   ├── processed/README.md
│   ├── topics/README.md
│   └── index/
│       ├── README.md
│       └── runtime-context-map.md
├── examples/
│   ├── example-canonical-doc.md
│   ├── example-raw-note.md
│   └── example-agent-adapter.md
└── validator/
    ├── __init__.py
    ├── validate.py                       # CLI entry point + core checks
    ├── schema.py                         # schema definition as data
    └── README.md

tests/kb_template/                        # NEW — top-level, mirrors tests/tools/ convention
└── test_validate.py

pyproject.toml                            # MODIFIED — add explicit `pyyaml` dependency
uv.lock                                   # MODIFIED — refreshed via `uv lock`
```

**Structure Decision**: This is a documentation-scaffold-plus-validator feature, not a
web/mobile/service app, so none of the template's Option 1/2/3 skeletons apply directly.
The concrete tree above is hand-authored: `kb-template/` is fully self-contained (its own
`pyproject.toml`, its own `validator/` package) so it can be copied out whole; only its test
suite lives outside it, at this repo's top-level `tests/kb_template/`, because Constitution
Principle IV requires tests to live in this repo's own `tests/` tree, and a test suite is
not part of what gets copied to other projects anyway.

## Complexity Tracking

*No violations — table not needed.*
