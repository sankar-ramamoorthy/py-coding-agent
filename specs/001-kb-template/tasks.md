---

description: "Task list for kb-template implementation"
---

# Tasks: kb-template — Portable Knowledge-Base Scaffold

**Input**: Design documents from `/specs/001-kb-template/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/validator-cli.md, quickstart.md

**Tests**: Included — Constitution Principle IV requires test coverage for new behavior.

**Organization**: Tasks are grouped by user story (US1/US2/US3 from spec.md) to enable
independent implementation and testing of each.

## Path Conventions

All paths below are relative to the repository root
(`C:\Users\bosto\dockerstuff\py-coding-agent`). `kb-template/` is the new, self-contained
scaffold; `tests/kb_template/` is this repo's own test package for it (per Constitution
Principle IV, not copied when kb-template/ is extracted elsewhere).

---

## Phase 1: Setup

**Purpose**: Project initialization and basic structure

- [X] T001 Create the `kb-template/` directory skeleton: `kb-template/docs/`,
      `kb-template/knowledge/raw/`, `kb-template/knowledge/processed/`,
      `kb-template/knowledge/topics/`, `kb-template/knowledge/index/`,
      `kb-template/examples/`, `kb-template/validator/`
- [X] T002 Create `kb-template/pyproject.toml` declaring `pyyaml` as its only dependency
- [X] T003 [P] Add an explicit `pyyaml` dependency to the root `pyproject.toml` and run
      `uv lock` to refresh `uv.lock` (already used transitively by `py_mono/skill/validator.py`,
      `py_mono/skill/base.py`, `py_mono/playbook/playbookregistry.py` — now declared)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The schema definition both the docs (US1) and the validator (US2/US3) depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Define the front-matter schema as data in `kb-template/validator/schema.py`
      (required fields, `type`/`status`/`authority` enum values, `canonical` bool,
      `related` list) per `data-model.md`
- [X] T005 [P] Create `kb-template/validator/__init__.py` (empty package init)

**Checkpoint**: Schema definition exists — user story implementation can now begin

---

## Phase 3: User Story 1 - Adopt the scaffold in a new or existing project (Priority: P1) 🎯 MVP

**Goal**: A contributor can copy `kb-template/` into an empty directory and immediately have
a documented, working schema + folder lifecycle, without consulting this repository.

**Independent Test**: Copy `kb-template/` into an empty directory; confirm the schema doc,
the four lifecycle folders, and the index files are present, readable, and self-explanatory.

### Implementation for User Story 1

- [X] T006 [P] [US1] Write `kb-template/README.md` — what the scaffold is, how to copy it
      elsewhere, and a quickstart pointer to running the validator
- [X] T007 [P] [US1] Write `kb-template/docs/schema.md` — human-readable documentation of
      the schema defined in `kb-template/validator/schema.py` (T004), single source of truth
      per spec FR-001
- [X] T008 [P] [US1] Write `kb-template/docs/promotion.md` — the promotion rule (status flip
      AND physical move out of `raw/`, never a silent edit) per spec FR-007
- [X] T009 [P] [US1] Write `kb-template/docs/authoring-rules.md` — canonical-document rules
      (front matter required, status/authority identified, cross-link related docs, record
      assumptions/exclusions, distinguish facts/rules/proposals/examples, no silent
      promotion) and raw-note rules (marked non-canonical, preserve source context, never
      treated as implementation authority) per spec FR-012/FR-013
- [X] T010 [P] [US1] Write `kb-template/knowledge/raw/README.md` — explains the raw stage
- [X] T011 [P] [US1] Write `kb-template/knowledge/processed/README.md` — explains the
      processed stage
- [X] T012 [P] [US1] Write `kb-template/knowledge/topics/README.md` — explains the topics
      (canonical) stage
- [X] T013 [P] [US1] Write `kb-template/knowledge/index/README.md` — navigation entrypoint
      for the knowledge base
- [X] T014 [P] [US1] Write `kb-template/knowledge/index/runtime-context-map.md` — routes a
      task category to the documents relevant to it, per spec FR-006
- [X] T015 [P] [US1] Write `kb-template/examples/example-canonical-doc.md` — filled-in
      example, `type: canonical-doc`, `status: canonical`, living under `knowledge/topics/`
      conventions (physically placed in `examples/` for the shipped template, cross-linking
      the other two examples via `[[wikilinks]]`)
- [X] T016 [P] [US1] Write `kb-template/examples/example-raw-note.md` — filled-in example,
      `type: raw-note`, `status: draft`, `canonical: false`
- [X] T017 [P] [US1] Write `kb-template/examples/example-agent-adapter.md` — filled-in
      example, `type: agent-adapter`

**Checkpoint**: At this point, User Story 1 is fully functional and testable independently —
the scaffold is complete, readable, and self-demonstrating (SC-001).

---

## Phase 4: User Story 2 - Author and validate a document (Priority: P2)

**Goal**: A contributor can run the validator against a document and get a clear pass, or a
clear, specific failure naming what's wrong (missing field, invalid enum, broken wikilink).

**Independent Test**: Run the validator against a valid document (passes); against documents
with a missing required field, an invalid enum value, and a broken wikilink (each fails with
a specific, correct message and non-zero exit).

### Tests for User Story 2 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T019–T021 don't exist yet)

- [X] T018 [US2] Write `tests/kb_template/test_validate.py` covering: a valid document
      passes; a document missing a required field fails naming that field; a document with
      an invalid enum value (`type`, `status`, or `authority`) fails naming the value and the
      allowed set; a document with a non-list `related` field fails; a document with an
      unresolvable `[[wikilink]]` fails naming the source file; a document with a resolvable
      `[[wikilink|alias]]`/`[[wikilink#anchor]]` passes

### Implementation for User Story 2

- [X] T019 [US2] Implement front-matter extraction (parse between `---` delimiters,
      `yaml.safe_load`, catch `yaml.YAMLError`) and schema validation against T004's
      `schema.py` in `kb-template/validator/validate.py`
- [X] T020 [US2] Implement wikilink extraction (regex `\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]`
      over document bodies) and case-insensitive filename-stem resolution against a
      whole-tree index in `kb-template/validator/validate.py` (depends on T019) — also
      strips fenced/inline code spans before matching, so illustrative `[[example]]`
      syntax in prose isn't mistaken for a real link (discovered during T023 verification)
- [X] T021 [US2] Implement the `ValidationResult` aggregator, per-file/summary console
      output, and `argparse` CLI entry point (positional `root`, defaults to own parent dir)
      with the exit codes from `contracts/validator-cli.md` in
      `kb-template/validator/validate.py` (depends on T019, T020)
- [X] T022 [P] [US2] Write `kb-template/validator/README.md` documenting the CLI invocation
      and what each check covers
- [X] T023 [US2] Run `pytest tests/kb_template/test_validate.py -v` and confirm all schema
      and wikilink test cases from T018 pass

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently — the validator
correctly checks schema compliance and wikilink resolution (SC-002 partial, SC-003 partial).

---

## Phase 5: User Story 3 - Promote a document from raw to canonical (Priority: P3)

**Goal**: The validator distinguishes a correct promotion (moved out of `raw/`, status
flipped) from an incorrect one (status flipped but the file left in `raw/`).

**Independent Test**: Validate a document moved to `knowledge/topics/` with `status:
canonical` (no violation reported); validate a document still in `knowledge/raw/` with
`status: canonical` (violation reported naming the file and its location).

### Tests for User Story 3 ⚠️

> Write these tests FIRST; ensure they FAIL before implementation (T025 doesn't exist yet)

- [X] T024 [US3] Add promotion-rule test cases to `tests/kb_template/test_validate.py`: a
      document under `knowledge/raw/` with `status: canonical` or `status: active` fails
      with a promotion-rule error naming the file and its path; the same document moved to
      `knowledge/topics/` passes

### Implementation for User Story 3

- [X] T025 [US3] Implement the promotion-rule check (status `canonical`/`active` AND path
      under `knowledge/raw/` → error) in `kb-template/validator/validate.py`, integrated into
      the `ValidationResult` produced by T021 (depends on T019, T021)
- [X] T026 [US3] Run `pytest tests/kb_template/test_validate.py -v` and confirm all
      promotion-rule test cases from T024 pass

**Checkpoint**: All three user stories are independently functional — the validator fully
implements schema, wikilink, and promotion-rule checks (SC-002 through SC-005).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Repo-wide regression checks and end-to-end proof the shipped scaffold works

- [X] T027 [P] Run `python -m compileall -q py_mono skills kb-template` — repo-wide syntax
      gate; also re-verifies `docs/ISSUES.md` ISS-001 (audit finding C-01). Exit 0 — ISS-001
      confirmed fixed. (Path corrected from `kb_template` to `kb-template` — the actual
      directory name uses a hyphen.)
- [X] T028 Run `pytest` (full suite) at the repo root — confirm nothing existing regressed.
      Found 3 pre-existing failures unrelated to this branch (1 collection error in
      `tests/test_listallpy_skill.py`, 2 assertion failures in `tests/tools/test_create_tool.py`)
      — confirmed pre-existing by reproducing identically with this branch's changes
      stashed. Logged as ISS-005. All 15 new `tests/kb_template/` tests pass; all
      pre-existing `tests/test_skill_approval.py` tests still pass — zero regressions
      introduced by this feature.
- [X] T029 Run the validator against the shipped scaffold, both invocation styles — must
      exit 0, proving the shipped scaffold is internally self-consistent (SC-002) and truly
      standalone-portable (SC-004, quickstart.md Scenario 1/6). Required adding
      `[tool.setuptools.packages.find]` to `kb-template/pyproject.toml` (setuptools flat-layout
      auto-discovery otherwise errors on multiple top-level dirs — `knowledge/`, `validator/`)
- [X] T030 Manually executed quickstart.md Scenarios 2–5 (missing field, invalid enum, broken
      wikilink, promotion violation) against scratch copies — each failed with the specific,
      correct message and exit code 1 documented in quickstart.md
- [ ] T031 Update `docs/ISSUES.md` (close ISS-001, mark ISS-004 done, add ISS-005 for the
      pre-existing test failures discovered in T028), and fill in `docs/SESSION_LOG.md`,
      `docs/CURRENT_FOCUS.md`, `docs/NEXT_ACTIONS.md` with the real end-of-session state per
      AGENTS.md's Session Completion section

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001's directory skeleton must exist) —
  BLOCKS all user stories
- **User Story 1 (Phase 3)**: Depends on Foundational (T004) for schema content to document;
  otherwise independent of US2/US3
- **User Story 2 (Phase 4)**: Depends on Foundational (T004's `schema.py`); does not depend
  on US1's prose docs, only on the same schema data
- **User Story 3 (Phase 5)**: Depends on US2 (T019, T021 — extends the same
  `validate.py`/`ValidationResult`)
- **Polish (Phase 6)**: Depends on all three user stories being complete

### Parallel Opportunities

- T003 (root `pyproject.toml`) can run in parallel with T001/T002 (different files)
- T005 (`__init__.py`) can run in parallel with T004 (different files, though both are quick)
- All of T006–T017 (US1) can run in parallel — each writes a distinct file, and none depend
  on each other, only on T004 for schema content
- T022 (validator README) can run in parallel with T019–T021 (different file)
- T027 can run in parallel with nothing else in Phase 6 (it's the first gate; T028–T031 are
  sequential after it in practice, since T031 records T027–T030's real results)

---

## Parallel Example: User Story 1

```bash
# After T004 (schema.py) is done, launch all of US1's doc-writing tasks together:
Task: "Write kb-template/README.md"
Task: "Write kb-template/docs/schema.md"
Task: "Write kb-template/docs/promotion.md"
Task: "Write kb-template/docs/authoring-rules.md"
Task: "Write kb-template/knowledge/raw/README.md"
Task: "Write kb-template/knowledge/processed/README.md"
Task: "Write kb-template/knowledge/topics/README.md"
Task: "Write kb-template/knowledge/index/README.md"
Task: "Write kb-template/knowledge/index/runtime-context-map.md"
Task: "Write kb-template/examples/example-canonical-doc.md"
Task: "Write kb-template/examples/example-raw-note.md"
Task: "Write kb-template/examples/example-agent-adapter.md"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (schema data)
3. Complete Phase 3: User Story 1 — the scaffold is copyable and self-explanatory
4. **STOP and VALIDATE**: copy `kb-template/` to an empty directory, read the README and
   schema doc cold
5. This alone already satisfies the pattern's original goal (a documented, reusable
   structure) even before the validator exists

### Incremental Delivery

1. Setup + Foundational → schema data ready
2. Add User Story 1 → scaffold readable and copyable (MVP)
3. Add User Story 2 → validator enforces schema + wikilinks
4. Add User Story 3 → validator enforces the promotion rule
5. Polish → repo-wide regression checks + end-to-end quickstart proof

---

## Notes

- [P] tasks touch different files with no dependency on an incomplete task
- Tests (T018, T024) are written before their corresponding implementation (T019–T021,
  T025) per Constitution Principle IV and this task list's own TDD ordering within each story
- Commit after each phase completes, not after each individual task (see plan.md's commit
  strategy — implementation lands as one or two commits, split by content-scaffold vs.
  validator-and-tests if needed)
