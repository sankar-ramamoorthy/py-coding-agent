# Quickstart: kb-template

Validation scenarios proving the feature works end-to-end. See `data-model.md` for field
rules and `contracts/validator-cli.md` for the full CLI contract.

## Prerequisites

- Python 3.10+ and `uv` available (already true in this repo's dev environment).
- Working directory: repo root, on the `kb-template` branch, after `/speckit-implement` has
  built `kb-template/`.

## Scenario 1: Shipped scaffold is self-consistent (SC-002)

```
uv run --project kb-template python -m validator.validate kb-template
```

**Expected**: exit code `0`; summary line reports 0 failed. Every shipped example under
`kb-template/examples/` and every index/README file passes schema and wikilink checks.

## Scenario 2: Missing required field is caught (SC-003)

```
cp kb-template/examples/example-raw-note.md /tmp/broken-missing-field.md
# remove the `authority:` line from the copy's front matter
uv run --project kb-template python -m validator.validate /tmp
```

**Expected**: exit code `1`; output names `authority` as a missing required field for
`broken-missing-field.md`.

## Scenario 3: Invalid enum value is caught (SC-003)

```
cp kb-template/examples/example-raw-note.md /tmp/broken-enum.md
# change `status: draft` to `status: published` in the copy
uv run --project kb-template python -m validator.validate /tmp
```

**Expected**: exit code `1`; output names `status` with the invalid value `published` and
lists the allowed values.

## Scenario 4: Broken wikilink is caught (SC-003)

```
cp kb-template/examples/example-canonical-doc.md /tmp/broken-link.md
# add `[[nonexistent-target]]` somewhere in the copy's body
uv run --project kb-template python -m validator.validate /tmp
```

**Expected**: exit code `1`; output names `nonexistent-target` as unresolved, with the
source file identified.

## Scenario 5: Promotion-rule violation is caught (SC-005)

```
mkdir -p /tmp/kb-scratch/knowledge/raw
cp kb-template/examples/example-canonical-doc.md /tmp/kb-scratch/knowledge/raw/leaked.md
# ensure the copy's status is `canonical` (the shipped example already is)
uv run python -m validator.validate /tmp/kb-scratch
```

**Expected**: exit code `1`; output flags `leaked.md` for having `status: canonical` while
still located under `knowledge/raw/`.

## Scenario 6: Portable outside this repo (SC-004)

```
cp -r kb-template /tmp/kb-template-copy
cd /tmp/kb-template-copy
uv run python -m validator.validate .
```

**Expected**: exit code `0`, with no dependency on py-coding-agent's own `uv` environment —
`kb-template-copy/pyproject.toml` supplies the only dependency (PyYAML) needed.

## Repo-level regression checks

```
python -m compileall -q py_mono skills kb_template
pytest
pytest tests/kb_template/ -v
```

**Expected**: all pass; nothing outside `kb-template/` and its own test file changed
behavior.
