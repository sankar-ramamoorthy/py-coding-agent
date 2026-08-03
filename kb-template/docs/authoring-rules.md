# Authoring Rules

## For canonical documents

A canonical document is one whose `status` is `canonical` or `active`. Hold it to a higher
bar than a raw note:

- **Front matter is required** — every field in `docs/schema.md`, filled in accurately, not
  copy-pasted placeholders.
- **Identify status and authority explicitly** — don't leave a reader to guess whether this
  is settled fact, house doctrine, a process description, or tool-specific advice; that's
  exactly what `status` and `authority` are for.
- **Cross-link related documents** — use the `related:` front-matter field and in-body
  `[[wikilinks]]` so a reader (or an agent) can discover the surrounding context instead of
  reading this document in isolation.
- **Record assumptions and exclusions** — state plainly what this document assumes to be
  true and what it deliberately does not cover. Silence reads as "this applies universally,"
  which is rarely what's meant.
- **Distinguish facts, rules, proposals, and examples** — a reader should never have to
  guess whether a sentence is describing what *is*, what *must be*, what *might be*, or an
  illustration of one case. Use headings or explicit framing ("Example:", "Proposed:") to
  keep these apart.
- **No silent promotion** — see `promotion.md`. A document does not become canonical by
  quietly editing its `status` field in place.

## For raw notes

A raw note is one whose `type` is `raw-note` and whose `status` is `draft` (the default for
anything newly captured):

- **Mark them non-canonical** — `canonical: false`, and don't let the document's tone imply
  more authority than that.
- **Preserve source context** — where did this come from (a conversation, a meeting, an
  external doc)? Keep enough of that context that a later reader can judge how much to trust
  it, rather than presenting it as if it were already synthesized.
- **Avoid treating them as implementation authority** — a raw note is an input to later
  synthesis, not a citable source of settled fact. Do not build downstream decisions on a
  raw note's claims without first promoting (or superseding) it through `knowledge/processed/`.
