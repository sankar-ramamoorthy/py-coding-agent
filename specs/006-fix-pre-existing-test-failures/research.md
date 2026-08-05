# Research: Fix pre-existing test failures

All three findings below were confirmed empirically against this repo's actual code and test
suite (not assumed) before any fix was written.

## Finding 1 — `listallpy` bypasses the tool abstraction

**Decision**: Rewrite `ListallpySkill.run()` to call `context.agent_tools["list_files"].run(path=".")`
and filter the returned JSON, instead of walking the filesystem directly.

**Rationale**: `tests/test_listallpy_skill.py` mocks `list_files` with a `Tool` fixture returning
a fixed JSON payload and expects the skill's output to reflect that payload. Reading
`skills/listallpy/skill.py` showed `run()` instead called
`Path(context.workspace_root).rglob("*.py")` directly — the mock was never consulted, so the
test observed the real repository's Python files. This is also a direct violation of ADR-016
("all file/process actions go through `context.agent_tools`"), independent of the test failure.
`skills/listallpy/SKILL.md` already declares `allowed_tools: [list_files]`, confirming the
intended design used the tool and the implementation simply didn't follow it.

**Alternatives considered**: Rewriting the tests to mock `Path.rglob` instead of `list_files`.
Rejected — this would encode the ADR-016 violation as correct behavior instead of fixing it, and
would diverge from every other skill's test style in this repo (all mock `context.agent_tools`,
none mock the filesystem module directly).

## Finding 2 — Approval-ledger hashing is checkout-platform-fragile

**Decision**: Normalize `\r\n` → `\n` in `approval_ledger.hash_file()` before hashing; regenerate
`skills/.approvals.json` under the fixed algorithm.

**Rationale**: `tests/test_skill_load_gating.py::test_all_real_approved_skills_still_load` failed
with `listallpy` reported as "has skill.py but is not approved/ledger-matched." Comparing the
ledger's recorded hash for `listallpy` against `git show HEAD:skills/listallpy/skill.py` (the
LF-normalized blob git actually tracks) showed an exact match — but the on-disk working-tree
file (with this checkout's CRLF line endings, from `core.autocrlf=true`) hashed differently
(760 bytes tracked vs. 783 bytes on disk). The approval was genuinely recorded against a
760-byte LF version; a later checkout on this same machine rewrote the working copy to CRLF,
invalidating the hash with zero actual content change.

To confirm this wasn't a one-off, every other currently-approved skill's ledger hash was checked
against its own git blob (i.e., what a from-scratch checkout on a platform using LF, such as a
typical Linux CI runner, would produce):

| Skill | Ledger hash matches LF git blob? |
| --- | --- |
| bug_fix | No |
| create_skill_py | No |
| doc_sync | No |
| generate_playbook | No |
| generate_skill | No |
| hello | No |
| listallpy | Yes |
| refactor_extract_function | No |
| scaffold_project | No |

7 of 9 would already fail an approval check on a Linux checkout of the exact same tracked
content. This directly threatens Milestone 6's CI item (`ISS-012`, same milestone): a GitHub
Actions Linux runner checking out this repo would see nearly every skill as suddenly
unapproved, for a reason unrelated to any real approval decision. Normalizing line endings
before hashing (rather than, say, forcing `.gitattributes` to pin one line-ending convention
repo-wide, or disabling `core.autocrlf`) fixes the root cause inside the one function
responsible for the guarantee, without depending on every future contributor's local git
configuration being correct.

**Alternatives considered**:
- Add a `.gitattributes` forcing LF for `*.py` — would fix new checkouts going forward but not
  retroactively, and depends on every contributor's git respecting it; the ledger itself should
  not depend on an out-of-band convention to give a correct answer.
- Re-approve only `listallpy` (narrow fix) — rejected once the table above showed this affects
  7 of 9 skills; a narrow fix would have left `ISS-012` (CI) walking directly into the same
  failure for every other skill.

## Finding 3 — `create_tool` message/contract mismatches

**Decision**: Update `create_tool`'s invalid-name message to
`"Error: tool name must be a valid Python identifier."` (matching this function's own
`"Error: ..."`-prefixed convention used for every other rejection path in the same function) and
its success message to include the written file's path (matching the sibling `write_file` tool's
`f"✅ File written successfully: {safe_path}"` convention). Corrected
`test_create_tool_writes_file_for_valid_name` and `test_create_tool_rejects_invalid_module_name`
to use code containing an actual function definition and to assert against the tool's real,
wrapped-`Tool`-schema output.

**Rationale**: `create_tool` wraps any given code in an auto-generated `Tool(...)` object with a
name/description/parameter schema inferred from a detected function signature — this is already
relied upon by three other, already-passing tests in the same file
(`test_create_tool_tool_declares_required_parameters`,
`test_create_tool_refuses_forbidden_pattern_code`,
`test_create_tool_writes_clean_code_successfully`), and is the safety-reviewed design from
`ISS-003` (static safety validation runs against the exact wrapped content before it's written).
The two failing tests predated that design and were never updated: one supplied code with no
`def` at all (which the current contract correctly rejects as `"Error: no function found."`),
and both asserted against message text the implementation never produced. Changing production
behavior to satisfy two outlying tests — when three other tests already depend on the current
behavior — would have been the wrong direction to reconcile the mismatch.

**Alternatives considered**: Make `create_tool` fall back to writing raw code verbatim when no
function is detected. Rejected — this is a security-relevant code path (ISS-003's static
safety/AST validation runs against the wrapped output); loosening it to accept arbitrary
non-function code was out of scope for a pre-existing-test-failure fix and not requested.
