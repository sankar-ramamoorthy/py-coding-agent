# Quickstart: Fix Skill/Tool Approval Gate

Validation scenarios proving the feature works end-to-end. See `data-model.md` for the
gating rules and `contracts/approval-gate-contract.md` for the full function contracts.

## Prerequisites

- Repo checked out on `fix-skill-tool-approval-gate` after `/speckit-implement` has landed
  the code.

## Automated — run first

```
uv run pytest tests/test_skill_load_gating.py tests/tools/test_tool_loader.py tests/tools/test_create_tool.py -v
```
**Expected**: all pass.

## Scenario 1: Reproduce the live-demonstrated bug, now fixed (FR-001, SC-001)

Using a `tmp_path`-based `SkillRegistry`, exactly reproducing this session's live demo:
a skill with `status: proposed` and a module-level marker in `skill.py`.

```python
registry = SkillRegistry(skills_dir=tmp_path)
registry.load()
```
**Expected**: the marker does NOT fire; the skill's metadata (name, description, status)
is still available via `list_skills()`.

## Scenario 2: Approved skill still executes normally (FR-001, Story 1 Scenario 3)

Same setup, `status: approved`, with a matching ledger entry.
**Expected**: the marker fires, exactly once, at `load()`.

## Scenario 3: Approval refuses unsafe content (FR-003, SC-002)

A skill.py containing a forbidden pattern (e.g. `os.system(`). Attempt `/approve` on it.
**Expected**: rejection message naming the issue; SKILL.md status and the ledger are both
unchanged; the marker never fires at any point.

## Scenario 4: Approval succeeds and triggers execution only after validation (SC-002)

A clean skill.py, `status: proposed`. Run `/approve`.
**Expected**: SKILL.md flips to `approved`, a ledger entry is written, and only now does a
subsequent load/reload execute the module.

## Scenario 5: Post-approval edit invalidates approval (FR-005, SC-003)

Approve a skill (Scenario 4), then modify its `skill.py` content afterward. Call
`reload_skill(name)` again.
**Expected**: the hash no longer matches the ledger entry; the skill reverts to
not-loaded; re-running `/approve` is required to restore it.

## Scenario 6: The 8 real, already-approved skills are unaffected (FR-006, SC-004)

Load the real `skills/` directory via `SkillRegistry(skills_dir=SKILLS_DIR).load()`.
**Expected**: all 8 skills (`hello`, `generate_skill`, `scaffold_project`, `bug_fix`,
`generate_playbook`, `doc_sync`, `create_skill_py`, `refactor_extract_function`) load and
run exactly as before; `skills/.approvals.json` now contains an entry for each, marked
`seeded: true` (confirming this was recognition, not a real review).

## Scenario 7: Dynamic tools off by default (FR-007, SC-005)

With `ENABLE_DYNAMIC_TOOLS` unset, start the app (or call the equivalent of
`build_base_tools`/`load_dynamic_tools`-gated startup logic).
**Expected**: none of the real files in `dynamic_tools/` load. Set
`ENABLE_DYNAMIC_TOOLS=true` — they load exactly as before.

## Scenario 8: Generated tool code is validated before it can exist (FR-008, SC-006)

```python
create_tool("evil", "import os\nos.system('echo hi')\n")
```
**Expected**: no file written to `dynamic_tools/`; an error string returned. A clean
equivalent call still writes successfully.

## Repo-level regression checks

```
python -m compileall -q py_mono
pytest
```
**Expected**: all pass; the two pre-existing `ISS-005` failures remain exactly as
documented (not fixed here, not worsened).
