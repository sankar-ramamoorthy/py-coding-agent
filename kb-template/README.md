# kb-template

A portable, framework-agnostic knowledge-base scaffold: a YAML front-matter schema plus
Obsidian-style markdown wikilinks, organized into a raw → processed → canonical lifecycle.

It exists so this documentation pattern is versioned once, here, instead of being
hand-built with drift each time a new project needs it.

## What's in here

```
kb-template/
├── docs/
│   ├── schema.md              # the front-matter schema (single source of truth)
│   ├── promotion.md           # the promotion rule
│   └── authoring-rules.md     # rules for canonical docs vs. raw notes
├── knowledge/
│   ├── raw/                   # captured, non-canonical by default
│   ├── processed/             # synthesized, pending promotion
│   ├── topics/                # canonical entities, cross-linked
│   └── index/                 # navigation entrypoint + task-to-docs routing
├── examples/                  # one filled-in sample document per document type
└── validator/                 # standalone Python validator (its own pyproject.toml)
```

Read `docs/schema.md` and `docs/promotion.md` next — everything else builds on those two.

## Using this scaffold in a new project

```
cp -r kb-template /path/to/your-project/kb-template
```

or, to keep it linked to this repo's history:

```
git subtree split --prefix=kb-template -b kb-template-split
```

Nothing inside `kb-template/` depends on this repository — it is self-contained and safe
to copy as-is.

## Validating your knowledge base

The validator checks that every document's front matter matches the schema and that every
`[[wikilink]]` resolves to a real file. It ships its own dependency declaration, so it runs
standalone wherever `kb-template/` ends up:

```
uv run python -m validator.validate .
```

Run from inside `kb-template/` (or the copy of it). With no argument, it defaults to
validating its own parent directory. See `validator/README.md` for the full CLI contract.
