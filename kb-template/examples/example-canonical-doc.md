---
title: Example Canonical Document
type: canonical-doc
status: canonical
project: kb-template
authority: doctrine
created: 2026-08-03
updated: 2026-08-03
canonical: true
related: [example-raw-note, example-agent-adapter]
---

# Example Canonical Document

This is a filled-in example of a canonical document, shipped so the validator has real
content to check itself against and so a new adopter has something concrete to clone.

## What makes this canonical

- Its `status` is `canonical` and it does not live inside `knowledge/raw/` — see
  [[../docs/promotion]] for why both conditions matter together.
- Its `authority` is `doctrine`: a strong default position, not an unbreakable invariant.
- It records its own assumptions and exclusions below, per [[../docs/authoring-rules]].

## Facts vs. rules vs. examples

- **Fact**: this file exists at `kb-template/examples/example-canonical-doc.md`.
- **Rule**: every canonical document MUST declare all nine front-matter fields from
  [[../docs/schema]].
- **Example**: the front matter at the top of this file is a worked example of a compliant
  block — copy its shape, not its content, when authoring a real document.

## Cross-references

This document is `related:` to [[example-raw-note]] (an example of the earlier lifecycle
stage this document might have come from) and [[example-agent-adapter]] (an example of a
different document `type` serving a different purpose).

## Assumptions and exclusions

- Assumes the reader has already read `kb-template/README.md` and `docs/schema.md`.
- Does not attempt to demonstrate every possible front-matter value — see `docs/schema.md`
  for the full enum lists.
