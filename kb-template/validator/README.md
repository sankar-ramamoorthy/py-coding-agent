# kb-template Validator

Checks every Markdown document under a scaffold root against three rules:

1. **Schema compliance** — all required front-matter fields present, enum fields
   (`type`, `status`, `authority`) hold an allowed value, `canonical` is a boolean, `related`
   is a list. See `../docs/schema.md`.
2. **Wikilink resolution** — every `[[target]]` in a document body resolves (by filename
   stem, case-insensitively) to a real file somewhere under the scaffold root.
3. **Promotion rule** — a document with `status: canonical` or `status: active` must not
   physically live under a `raw/` folder. See `../docs/promotion.md`.

## Running it

```
uv run python -m validator.validate [ROOT]
```

Run from inside `kb-template/` (this directory's parent). `ROOT` is optional and defaults to
`kb-template/` itself, so a bare invocation validates the scaffold you're standing in:

```
cd kb-template
uv run python -m validator.validate .
```

From this repo's root, invoke it against the copy this repo ships via `uv`'s project flag:

```
uv run --project kb-template python -m validator.validate kb-template
```

## Output

One line per file (`OK <path>` or `FAIL <path>` with indented `schema:`/`promotion:`/
`wikilink:` error lines beneath it), followed by a summary line
(`N files checked, M passed, K failed`).

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | every file passed all three checks |
| `1` | at least one file failed at least one check |
| `2` | the given root does not exist or is not a directory |

Full contract: `../../specs/001-kb-template/contracts/validator-cli.md`.
