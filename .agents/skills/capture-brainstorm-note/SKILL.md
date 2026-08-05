---
name: "capture-brainstorm-note"
description: "Structure messy notes, pasted chat output, app-friction reports, or rough ideas into a raw brainstorming Markdown note. Use when the user wants to capture thinking in this project's knowledge base without needing to provide front matter, filenames, or note structure."
---

# Capture Brainstorm Note

## Purpose

Turn unstructured thinking into a raw, non-canonical brainstorm note that can be processed
later.

## Scope note

This skill's front-matter shape is written for **this project's** knowledge base
(`kb-template/`), whose validator (`kb-template/validator/schema.py`) enforces a specific,
enum-constrained schema. A copy of this skill dropped into another project should re-check that
project's own schema before reusing the "Required Note Shape" below verbatim — the shape here is
intentionally narrower than a generic version would be.

## Workflow

1. Target directory: this project's knowledge base root is `kb-template/knowledge/raw/`. Use it
   directly. If it's ever missing, ask for the target directory before writing rather than
   guessing.
2. Infer a concise title and topic slug from the note. This schema has no `tags` field — fold
   topic keywords into the title instead of adding untracked front-matter fields.
3. Create one Markdown file in `kb-template/knowledge/raw/`.
   - Filename pattern: `brainstorm-YYYYMMDD-short-topic.md`.
   - Use the current local date for `created` and `updated`.
4. Preserve the user's original thinking under `Raw Input`.
   - Lightly clean obvious copy/paste artifacts only when they obscure meaning.
   - Keep uncertainty, contradictions, and rough ideas visible.
5. Organize the note into the standard sections below.
6. Stop after creating the raw brainstorm note unless the user separately asks for processing,
   promotion, issues, ADRs, or canonical-page edits.

## Required Note Shape

Front matter must satisfy `kb-template/docs/schema.md` exactly — all 9 fields, valid enum
values, nothing invented:

```markdown
---
title: Example Brainstorm Title
type: raw-note
status: draft
project: py-coding-agent
authority: tool-specific-guidance
created: YYYY-MM-DD
updated: YYYY-MM-DD
canonical: false
related: []
---

# Example Brainstorm Title

## Trigger

What caused this thought or session.

## Raw Input

The user's original note, pasted output, or rough thought.

## Observations

- What happened, what felt wrong, or what was noticed.

## Ideas

- Possible fixes or directions, including incomplete ideas.

## Questions

- Open uncertainties or decisions needed.

## Concerns

- Risks, tradeoffs, architectural boundaries, or process concerns.

## Possible Next Outputs

- Issue candidate
- Topic page update
- ADR candidate
- Spec Kit spec candidate
- No action
```

`type` must be one of `canonical-doc`, `agent-adapter`, `raw-note`, `adr` — always `raw-note`
for this skill's output. `status` must be one of `draft`, `active`, `canonical`, `deprecated` —
always `draft` here. `authority` must be one of `invariant`, `doctrine`, `process`,
`tool-specific-guidance` — pick whichever actually fits the note's content (a tool-behavior
quirk is `tool-specific-guidance`; a workflow observation is `process`).

## Boundaries

- Do not treat brainstorm notes as canonical knowledge.
- Do not update `kb-template/knowledge/index/`, `kb-template/knowledge/topics/`, or any other
  project doc (`README.md`, `AGENTS.md`, etc.).
- Do not move raw notes to `kb-template/knowledge/processed/` — see
  `kb-template/docs/promotion.md` for the explicit promotion rule this would otherwise violate.
- Do not create ADRs, GitHub issues, or Spec Kit specs unless the user explicitly asks — listing
  them under "Possible Next Outputs" is not the same as creating them.
- Do not over-resolve the brainstorm. Preserve messy thinking while making it easy to process
  later. See `kb-template/docs/authoring-rules.md` for how raw notes should read.

## Defaults

- Prefer ASCII Markdown.
- Write directly into `kb-template/knowledge/raw/` — no extra subdirectory.
- Use wikilinks (`[[document-name]]`) only when an obvious existing document is named by the
  user or visible in the current context.
- If the user provides app friction, make the trigger concrete and record observed workflow
  pain separately from solution ideas.
