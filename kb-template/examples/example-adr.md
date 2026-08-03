---
title: Example Architecture Decision Record
type: adr
status: active
project: kb-template
authority: doctrine
created: 2026-08-03
updated: 2026-08-03
canonical: true
related: [example-canonical-doc]
---

# Example Architecture Decision Record

This is a filled-in example of an `adr` document: a record of a specific decision, framed
around the choice made and why, rather than general reference documentation.

## What distinguishes an adr from a canonical-doc

- **Purpose**: a canonical-doc ([[example-canonical-doc]]) records settled knowledge about
  how something works or should be done; an `adr` records the history of a specific,
  point-in-time decision — what was chosen, what alternatives were rejected, and why. An
  ADR's content doesn't change when circumstances change; instead, a new ADR supersedes it.
- **Structure**: ADRs conventionally follow a `Status` / `Context` / `Decision` /
  `Consequences` shape (illustrated below), distinct from a canonical-doc's freer structure.

## Status

Accepted.

## Context

(Placeholder: in a real ADR, this section states the problem or forces at play that made a
decision necessary — constraints, trade-offs under consideration, prior approaches that
didn't hold up.)

## Decision

(Placeholder: this section states the choice made, in one or two sentences, without hedging.)

## Consequences

(Placeholder: this section states what becomes easier or harder as a result — including
trade-offs deliberately accepted, not just benefits.)

## Note on this project's own ADRs

If the project adopting `kb-template/` already has its own ADR convention (as py-coding-agent
does, in `docs/adr/`), it is reasonable to keep using that convention for the project's real
architecture decisions rather than duplicating them here under `type: adr`. This example
exists so the schema's `adr` type is demonstrated and validated, not to mandate migrating an
existing ADR practice onto this scaffold.
