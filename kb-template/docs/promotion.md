# Promotion Rule

A document becomes canonical only when **both** of the following happen together, in the
same change:

1. Its `status` field flips to `canonical` (or `active`), **and**
2. It physically moves out of `knowledge/raw/` (into `knowledge/processed/` or
   `knowledge/topics/`).

Neither condition alone is a promotion:

- Flipping `status` to `canonical` while leaving the file inside `knowledge/raw/` is **not**
  a valid promotion — it is a silent edit that claims authority the document's location
  contradicts. The validator treats this as an error.
- Moving a file out of `knowledge/raw/` without changing its `status` does not make it
  canonical either — it just changes its lifecycle stage; the status field still governs
  whether it's trusted as settled.

## Why this rule exists

Promotion is meant to be a visible, deliberate event — something a reviewer notices in a
diff (a file move plus a status change), not something that can happen by quietly editing
one line of front matter in place. This is what makes "canonical" mean something: a reader
can trust that anything under `knowledge/topics/` with `status: canonical` or `status:
active` went through an explicit promotion, not an unreviewed edit.

## Typical lifecycle

```
knowledge/raw/my-note.md            (status: draft)
        │  synthesize, still not settled
        ▼
knowledge/processed/my-note.md      (status: draft or active)
        │  explicit decision: this is now settled
        │  move the file AND flip status in the same change
        ▼
knowledge/topics/my-note.md         (status: canonical or active)
```

A document may also be marked `status: deprecated` at any stage, in any folder — deprecation
is a separate signal from the raw → canonical promotion path, not a stage in it.
