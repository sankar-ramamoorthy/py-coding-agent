# Phase 1 Data Model: kb-template

## Document

A Markdown file with a YAML front-matter block delimited by `---` on the first and second
lines matching that pattern in the file.

| Field | Type | Required | Constraint |
|-------|------|----------|------------|
| `title` | string | yes | non-empty |
| `type` | enum(string) | yes | one of `canonical-doc`, `agent-adapter`, `raw-note`, `adr` |
| `status` | enum(string) | yes | one of `draft`, `active`, `canonical`, `deprecated` |
| `project` | string | yes | non-empty (name of the owning/consuming project; may be a placeholder like `kb-template` itself inside the shipped examples) |
| `authority` | enum(string) | yes | one of `invariant`, `doctrine`, `process`, `tool-specific-guidance` |
| `created` | string (date) | yes | ISO 8601 date |
| `updated` | string (date) | yes | ISO 8601 date |
| `canonical` | boolean | yes | `true` or `false` |
| `related` | list(string) | yes (may be empty list) | each entry is a plain document name, not a bracketed wikilink string |

**Validation rules** (from spec FR-001–FR-004, FR-007):
- All 9 fields must be present; missing any is a schema error naming the field.
- `type`, `status`, `authority` must hold one of their enumerated values; any other value is
  a schema error naming the field, the invalid value, and the allowed set.
- `canonical` must be a YAML boolean, not a string like `"true"`.
- `related` must be a YAML list (empty list is valid); a non-list value is a schema error.
- **Promotion-rule cross-check**: if `status` is `canonical` or `active`, the document's
  physical path must not be under `knowledge/raw/` — violating this is a distinct
  promotion-rule error, separate from a schema error.

## Folder stage

Not a data entity with fields — a structural classification derived from a document's path:

| Stage | Path prefix | Meaning |
|-------|-------------|---------|
| raw | `knowledge/raw/` | Captured, non-canonical by default |
| processed | `knowledge/processed/` | Synthesized, pending promotion |
| topics | `knowledge/topics/` | Canonical entities, cross-linked |

A document's stage is read from its path at validation time; it is not a front-matter field.

## Wikilink

An in-body reference, not a front-matter field. Regex-extracted from document text:

```text
\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]
```

- Capture group 1 is the link target (a filename stem, not a path).
- Optional `|alias` or `#anchor` suffixes are recognized and ignored for resolution purposes.
- Resolution: match target against an index of every document's filename stem under the
  scaffold root, case-insensitively; a case-mismatched match is reported as a warning; no
  match under any case is a wikilink error naming the source file and (if available) line
  number.

## ValidationResult

The validator's internal/output data shape, one instance per checked file:

| Field | Type | Meaning |
|-------|------|---------|
| `path` | string | file path relative to the scaffold root |
| `valid` | boolean | true only if no errors of any kind were found for this file |
| `schema_errors` | list(string) | missing-field / invalid-enum / wrong-type messages |
| `promotion_errors` | list(string) | promotion-rule violation messages, if any |
| `wikilink_errors` | list(string) | unresolved-wikilink messages, if any |

An aggregate run produces a list of `ValidationResult`, one per Markdown file under the
scaffold root; overall process exit code is non-zero if any result has `valid: false`.

## State transitions (promotion lifecycle)

```text
[raw/, status: draft]
        │  (author decides doc is synthesized but not yet settled)
        ▼
[processed/, status: draft or active]
        │  (explicit human decision: promote)
        │  action = move file out of raw|processed AND flip status field
        ▼
[topics/, status: canonical or active]
```

- A transition is only valid when the physical move and the status flip happen together in
  the same change — the validator's promotion-rule check exists specifically to catch the
  case where only the status field was flipped (silent promotion), per spec FR-007.
- `status: deprecated` may apply to a document in any stage; it does not by itself imply the
  document must move — deprecation is a separate axis from the raw→canonical promotion path.
