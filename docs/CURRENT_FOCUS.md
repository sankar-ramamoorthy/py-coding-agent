# Current Focus

## Active branch
`kb-template`

## What's being worked on right now
Building `kb-template/` (a portable, self-contained knowledge-base scaffold) plus a
repo process bootstrap (`docs/ISSUES.md`, the four session-handoff docs, and the
Completion Report Format documented in AGENTS.md's Session Completion section).

## Why
Two other projects (TradeForge-KnowledgeBase, AITrader) have each hand-built a similar
YAML-front-matter + Obsidian-markdown documentation pattern, with drift each time. This
versions the pattern once, here, for reuse via `cp -r` / `git subtree split`.

## Not being worked on right now (explicitly out of scope)
- Splitting `kb-template/` into its own repo
- Migrating TradeForge-KnowledgeBase or AITrader onto this schema
- Wiring the validator into this repo's own CI/pre-commit
- ISS-002 / ISS-003 (sandbox/execution security issues) — unrelated to this branch
