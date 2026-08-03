# Current Focus

## Active branch
`kb-template` — implementation complete, awaiting review before push/PR.

## What was just finished
`kb-template/` (portable knowledge-base scaffold) and the repo process bootstrap
(`docs/ISSUES.md`, session-handoff docs, Completion Report Format) are both done. See
`docs/SESSION_LOG.md`'s 2026-08-03 entry for the full completion report.

## Why
Two other projects (TradeForge-KnowledgeBase, AITrader) have each hand-built a similar
YAML-front-matter + Obsidian-markdown documentation pattern, with drift each time. This
versions the pattern once, here, for reuse via `cp -r` / `git subtree split`.

## Not being worked on right now (explicitly out of scope)
- Splitting `kb-template/` into its own repo
- Migrating TradeForge-KnowledgeBase or AITrader onto this schema
- Wiring the validator into this repo's own CI/pre-commit
- ISS-002 / ISS-003 (sandbox/execution security issues, formerly audit C-02/C-03)
- ISS-005 (pre-existing, unrelated test failures — logged, not fixed)
