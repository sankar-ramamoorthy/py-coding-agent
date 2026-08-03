# Front-Matter Schema

Every document in this knowledge base starts with a YAML front-matter block delimited by
`---` on its own line, both opening and closing:

```yaml
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
```

## Fields

| Field | Type | Required | Allowed values |
|-------|------|----------|-----------------|
| `title` | string | yes | any non-empty string |
| `type` | string (enum) | yes | `canonical-doc`, `agent-adapter`, `raw-note`, `adr` |
| `status` | string (enum) | yes | `draft`, `active`, `canonical`, `deprecated` |
| `project` | string | yes | the name of the project this document belongs to |
| `authority` | string (enum) | yes | `invariant`, `doctrine`, `process`, `tool-specific-guidance` |
| `created` | date | yes | ISO 8601 (`YYYY-MM-DD`) |
| `updated` | date | yes | ISO 8601 (`YYYY-MM-DD`) |
| `canonical` | boolean | yes | `true` or `false` |
| `related` | list of strings | yes (may be empty: `[]`) | plain document names, e.g. `[topic-a, topic-b]` — not bracketed `[[wikilink]]` strings |

### `type`

- **`canonical-doc`** — settled, authoritative documentation.
- **`agent-adapter`** — a document written specifically to brief an AI agent on a topic.
- **`raw-note`** — captured but not yet synthesized or reviewed.
- **`adr`** — an architecture/decision record.

### `status`

- **`draft`** — being written, not yet reviewed.
- **`active`** — currently in effect and trusted, but may still evolve.
- **`canonical`** — settled, authoritative. See `promotion.md` for how a document earns this.
- **`deprecated`** — superseded; kept for history, not for current guidance.

### `authority`

- **`invariant`** — must not be violated; changes require explicit, deliberate review.
- **`doctrine`** — the house position; strong default, can be revisited with reason.
- **`process`** — describes how work gets done, not a fact about the world.
- **`tool-specific-guidance`** — applies only when using a particular tool or system.

## Wikilinks

Inside a document's body (not its front matter), link to another document with
`[[document-name]]`, optionally `[[document-name|display text]]` or
`[[document-name#section]]`. Links resolve by filename stem, case-insensitively. The
`related:` front-matter field lists the same target names as plain strings, without the
`[[...]]` brackets — that syntax is reserved for prose.

See `promotion.md` for the rule governing when `status` may be `canonical`, and
`authoring-rules.md` for how canonical documents and raw notes should be written.
