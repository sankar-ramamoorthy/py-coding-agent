# Contract: kb-template validator CLI

The validator is the scaffold's only external-facing interface (a CLI, not a library API or
network service). This documents its contract.

## Invocation

```
uv run python -m validator.validate [ROOT]
```

- `ROOT` (optional, positional): path to the scaffold root to validate. Defaults to the
  validator's own parent directory (i.e. `kb-template/` itself) when omitted, so a bare
  invocation from inside a copied scaffold validates that scaffold with no arguments needed.
- From this repo's root, invoked as: `uv run --project kb-template python -m validator.validate kb-template`

## Behavior

1. Walks `ROOT` for every `*.md` file.
2. For each file, runs three checks (see `data-model.md` for the underlying rules):
   - Front-matter schema check
   - Promotion-rule check
   - Wikilink resolution check
3. Prints a per-file summary line: `OK <path>` or `FAIL <path>` followed by indented error
   messages for that file.
4. Prints a final summary count: `N files checked, M passed, K failed`.

## Exit codes

| Code | Meaning |
|------|---------|
| `0` | Every file passed all three checks |
| `1` | At least one file failed at least one check |
| `2` | `ROOT` does not exist or is not a directory |

## Output stability

Error message wording is not a stable contract (may be reworded for clarity across
versions); the exit-code contract above and the three check categories are stable — a
consumer scripting against this CLI (e.g. a future CI/pre-commit wiring, explicitly out of
scope for this feature) should key off exit code, not message text.
