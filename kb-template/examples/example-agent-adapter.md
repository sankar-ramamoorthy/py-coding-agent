---
title: Example Agent Adapter
type: agent-adapter
status: active
project: kb-template
authority: tool-specific-guidance
created: 2026-08-03
updated: 2026-08-03
canonical: true
related: [example-canonical-doc]
---

# Example Agent Adapter

This is a filled-in example of an `agent-adapter` document: written specifically to brief an
AI agent on a topic, rather than to serve as general human-facing documentation.

## What distinguishes an agent-adapter from a canonical-doc

- **Purpose**: a canonical-doc ([[example-canonical-doc]]) records settled knowledge for any
  reader; an agent-adapter packages that same kind of knowledge specifically for consumption
  by an agent — often more terse, more structured, and framed around what an agent needs to
  decide or do next.
- **Authority**: this example uses `tool-specific-guidance` rather than `doctrine`, since
  agent-adapter documents commonly apply only when a particular agent or tool is in play,
  not universally.

## Example adapter content

```
When asked to validate this knowledge base, run:
  uv run python -m validator.validate .
from inside kb-template/. Report the exit code and any per-file errors verbatim; do not
summarize away specific missing-field or broken-wikilink messages.
```

This is illustrative — a real agent-adapter would contain whatever briefing an agent
actually needs for the task it supports.
