---
title: Example Raw Note
type: raw-note
status: draft
project: kb-template
authority: process
created: 2026-08-03
updated: 2026-08-03
canonical: false
related: [example-canonical-doc]
---

# Example Raw Note

This is a filled-in example of a raw note — captured, non-canonical by default, per
[[../knowledge/raw/README]].

## Source context

(In a real raw note, this section would say where the material came from — a meeting, a
conversation, an external document — so a later reader can judge how much to trust it before
it's been synthesized. This example simply notes that it was written as a shipped sample for
`kb-template`.)

## Why this is not canonical

- `status: draft` and `canonical: false` mark it explicitly as not-yet-settled.
- It should not be cited as implementation authority — see [[../docs/authoring-rules]].
- If this note matured into settled knowledge, it would move to `knowledge/processed/` or
  `knowledge/topics/` and have its `status` flipped in that same move — see
  [[../docs/promotion]]. Flipping `status` here without moving the file would be exactly the
  silent-promotion failure the validator's promotion-rule check exists to catch.

See [[example-canonical-doc]] for what this note might look like after promotion.
