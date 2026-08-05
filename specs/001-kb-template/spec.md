# Feature Specification: kb-template — Portable Knowledge-Base Scaffold

**Feature Branch**: `kb-template`

**Created**: 2026-08-03

**Status**: Draft

**Input**: User description: "Add a self-contained, top-level kb-template/ directory: a portable, framework-agnostic knowledge-base scaffold (YAML front-matter + Obsidian-style markdown wikilinks) that other projects can copy via `cp -r` or `git subtree split`, so a documentation pattern already hand-built inconsistently across other unrelated projects exists once, versioned, here. Must provide a canonical YAML front-matter schema, a raw/processed/topics folder lifecycle with an index and runtime-context-map, an explicit promotion rule, a standalone Python validator checking schema compliance and wikilink resolution, authoring-rules documentation, and one example per document type. Must not depend on this repo's runtime code or ship project-specific content. Out of scope: repo split, UI/rendering, migrating other projects onto the schema, wiring into this repo's own CI/pre-commit."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Adopt the scaffold in a new or existing project (Priority: P1)

A contributor starting a new project, or retrofitting an existing one, wants a working
knowledge-base structure — a documented front-matter schema and a folder lifecycle for
raw/processed/canonical documents — without inventing it from scratch or copying it
inconsistently from memory the way it was previously hand-built across two other projects.

**Why this priority**: This is the entire reason the feature exists — without it, nothing
else in the scaffold has anywhere to be used. It is the minimum viable slice: a contributor
can copy the directory and immediately have a documented, working structure.

**Independent Test**: Can be fully tested by copying `kb-template/` into an empty directory
and confirming the schema doc, folder lifecycle, and index files are present, readable, and
self-explanatory without consulting this repository.

**Acceptance Scenarios**:

1. **Given** an empty target directory, **When** `kb-template/` is copied into it, **Then**
   the schema documentation, the four lifecycle folders (`raw/`, `processed/`, `topics/`,
   `index/`), and the navigation/routing index files are all present and readable.
2. **Given** the copied scaffold, **When** a contributor reads `kb-template/README.md`,
   **Then** they understand what the scaffold is, how to use it, and how to run the
   validator, without needing to read any other file first.

---

### User Story 2 - Author and validate a document (Priority: P2)

A contributor writes a new document (a raw note or a canonical doc) following the schema,
then runs the validator before committing, to confirm the front matter is well-formed and
every wikilink in the document resolves to a real file.

**Why this priority**: This is what makes the pattern enforceable rather than just
documented convention — the validator is the second half of the feature's value, after the
schema itself exists (P1).

**Independent Test**: Can be fully tested by creating a document with valid front matter and
running the validator against it — it passes. Creating a document with a missing required
field, an invalid enum value, or a broken wikilink — the validator reports the specific
problem and exits non-zero.

**Acceptance Scenarios**:

1. **Given** a document with complete, valid front matter and only resolvable wikilinks,
   **When** the validator runs, **Then** it reports success and exits zero.
2. **Given** a document missing a required front-matter field, **When** the validator runs,
   **Then** it reports exactly which field is missing and exits non-zero.
3. **Given** a document with an invalid value for an enum field (e.g. an unrecognized
   `status`), **When** the validator runs, **Then** it reports the invalid value and the
   allowed values, and exits non-zero.
4. **Given** a document containing a `[[wikilink]]` to a file that does not exist anywhere
   in the scaffold, **When** the validator runs, **Then** it reports the unresolved link
   with the source file, and exits non-zero.

---

### User Story 3 - Promote a document from raw to canonical (Priority: P3)

A contributor has a raw note that has matured into settled knowledge. They move it out of
`knowledge/raw/` into `knowledge/topics/` and flip its `status` field to `canonical` or
`active`, making the promotion an explicit, visible event rather than a silent edit.

**Why this priority**: This encodes the scaffold's core doctrine (no silent promotion) but
depends on P1 and P2 already existing — it's a specific workflow layered on top of the
schema and validator, not new mechanism.

**Independent Test**: Can be fully tested by promoting one example document (moving file +
flipping status) and confirming the validator no longer flags it, versus leaving a document
with a flipped status still inside `raw/` and confirming the validator does flag it.

**Acceptance Scenarios**:

1. **Given** a document moved from `knowledge/raw/` to `knowledge/topics/` with its `status`
   flipped to `canonical`, **When** the validator runs, **Then** it reports no promotion-rule
   violation for that document.
2. **Given** a document still inside `knowledge/raw/` but with `status` set to `canonical` or
   `active`, **When** the validator runs, **Then** it reports a promotion-rule violation
   naming the file and its current location.

---

### Edge Cases

- What happens when a document's front matter cannot be parsed as YAML at all (malformed
  syntax)? The validator reports a parse failure for that file rather than crashing, and
  continues checking the remaining documents.
- What happens when a document has no front matter (no `---` delimiters)? The validator
  reports it as missing all required fields rather than crashing.
- What happens when `related` in the front matter is not a list? The validator reports a
  type error for that field.
- What happens when a wikilink includes an alias or anchor (`[[target|alias]]`,
  `[[target#section]]`)? The validator resolves against the target portion only.
- What happens when the scaffold is copied to a location with no network/parent-project
  Python environment available? The validator still runs, because it ships its own
  `pyproject.toml` declaring its only dependency (PyYAML).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The scaffold MUST define a single canonical YAML front-matter schema,
  documented in one place inside `kb-template/`, with required fields: `title`, `type`,
  `status`, `project`, `authority`, `created`, `updated`, `canonical`, `related`.
- **FR-002**: The `type` field MUST be constrained to one of: `canonical-doc`,
  `agent-adapter`, `raw-note`, `adr`.
- **FR-003**: The `status` field MUST be constrained to one of: `draft`, `active`,
  `canonical`, `deprecated`.
- **FR-004**: The `authority` field MUST be constrained to one of: `invariant`, `doctrine`,
  `process`, `tool-specific-guidance`.
- **FR-005**: The scaffold MUST provide a folder lifecycle: `knowledge/raw/` (non-canonical
  by default), `knowledge/processed/` (pending promotion), `knowledge/topics/` (canonical,
  cross-linked), `knowledge/index/`.
- **FR-006**: `knowledge/index/` MUST include a `README.md` (navigation entrypoint) and a
  `runtime-context-map.md` (routes a task category to the documents relevant to it).
- **FR-007**: A document MUST be treated as canonical only when its `status` is `canonical`
  or `active` AND it physically resides outside `knowledge/raw/` — this promotion event MUST
  NOT be satisfied by an in-place status edit alone.
- **FR-008**: The scaffold MUST ship a validator that checks every document's front matter
  against the schema (required fields present; enum fields hold valid values).
- **FR-009**: The validator MUST check that every `[[wikilink]]` appearing in a document's
  body resolves to an actual file within the scaffold.
- **FR-010**: The validator MUST check the promotion rule (FR-007) and report violations.
- **FR-011**: The validator MUST be runnable standalone, independent of any parent project's
  environment — it ships its own `pyproject.toml` declaring PyYAML as its only dependency,
  and is invocable via `uv run`.
- **FR-012**: The scaffold MUST document authoring rules for canonical documents: front
  matter required, status and authority identified, related documents cross-linked,
  assumptions and exclusions recorded, facts/rules/proposals/examples distinguished, no
  silent promotion.
- **FR-013**: The scaffold MUST document authoring rules for raw notes: marked non-canonical,
  source context preserved, never treated as implementation authority.
- **FR-014**: The scaffold MUST include one filled-in example document per `type` value
  (`canonical-doc`, `raw-note`, `agent-adapter`, `adr`) so the pattern is self-demonstrating.
- **FR-015**: The scaffold MUST NOT import from or depend on any parent project's runtime
  source code.
- **FR-016**: The scaffold MUST NOT contain project-specific canonical content — schema,
  folder skeleton, index stubs, examples, and validator only.

### Key Entities

- **Document**: a Markdown file with YAML front matter conforming to the schema; identified
  by its `type`, positioned in the lifecycle by its `status` and physical folder location.
- **Folder stage**: `raw/`, `processed/`, or `topics/` — represents a document's current
  position in the raw → processed → canonical lifecycle.
- **Wikilink**: an in-body `[[target]]` cross-reference between two documents.
- **Validation Result**: the outcome of checking one document — schema errors, wikilink
  errors, and promotion-rule errors, if any.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A contributor can locate and understand the front-matter schema and the
  folder lifecycle from a single README read, without consulting any file outside
  `kb-template/`.
- **SC-002**: Running the validator against the shipped scaffold (its own example documents
  and index files) reports zero errors — the shipped template is internally self-consistent.
- **SC-003**: In 100% of tested failure cases (missing required field, invalid enum value,
  broken wikilink, promotion-rule violation), the validator reports specifically what is
  wrong and exits non-zero.
- **SC-004**: The scaffold, copied into a new location outside this repository with no
  modification, runs its validator successfully there.
- **SC-005**: A document promoted correctly (moved out of `raw/`, status flipped) is never
  flagged as a violation; a document left in `raw/` with a flipped status is flagged, in
  100% of tested cases.

## Assumptions

- Contributors have Python 3.10+ and `uv` available (already true for this repository).
- "Portable" means copyable via `cp -r` or `git subtree split` and runnable via its own
  declared dependency — it does not require working with zero Python runtime installed
  anywhere.
- Wikilink resolution matches by filename stem, case-insensitively (with a warning on case
  mismatch), since Obsidian-style wikilinks are conventionally short names, not full paths.
- The `related` front-matter field holds a list of plain document names; the `[[...]]`
  bracket syntax is reserved for in-body prose wikilinks only.
- Integrating the validator into this repository's own CI/pre-commit is explicitly out of
  scope for this feature — the scaffold must merely be capable of being wired in elsewhere.
- Splitting `kb-template/` into its own repository, and migrating other internal
  knowledge-base projects onto this schema, are explicitly deferred to future, separate work.
