# Skill Catalog

All skills are invoked via `/skill <name> [args] [flags]`.  
All skills follow ADR-016: use `agent_tools` only, no direct syscalls.  
All skills require `status: approved` in `SKILL.md` to run.

**Global flags:**
- `dry_run:true` — Show diff/preview without writing files
- `--overwrite` — Replace existing output file, for `create_skill_py`

---

## 1. bug_fix

**Purpose:** Apply minimal patch to fix a Python error from stack trace. Runs pytest and rolls back if tests fail.

**Location:** `skills/bug_fix/`

**Trigger:** `/skill bug_fix <error> file:<path> [line:<num>] [dry_run:<true|false>]`

**Allowed tools:** `read_file`, `write_file`, `edit_file`, `shell`

**Constraints:**
- No file deletion
- No new dependencies  
- No editing `.env` or key files
- Must pass pytest before completing. Auto-rollback on test failure.

**Args:**
| Arg | Required | Description | Example |
| --- | --- | --- | --- |
| `error` | Yes | Error message or exception type | `KeyError:'user'` |
| `file:` | Yes | Path to buggy file | `file:src/auth.py` |
| `line:` | No | Line number from stack trace. Default: 1 | `line:42` |
| `dry_run:` | No | Show diff only | `dry_run:true` |

**Example:**
```bash
/skill bug_fix KeyError:'user' file:src/auth.py line:42 dry_run:true
Output: Shows diff replacing `d['user']` with `d.get('user')`
/skill bug_fix KeyError:'user' file:src/auth.py line:42 dry_run:false
Applies patch, writes regression test to `tests/test_auth_regression.py`, runs pytest.

*Failure modes:*
❌ Missing required argument. Usage: /skill bug_fix <error> file:<path> [line:<num>]
❌ Failed to read src/auth.py: File not found
[BUG_FIX] Tests failed after fix. Rolled back.
---

## 2. refactor_extract_function

*Purpose:* Extract a block of code into a new helper function. Preserves behavior. Generates test for extracted function.

*Location:* `skills/refactor_extract_function/`

*Trigger:* `/skill refactor_extract_function file:<path> start:<num> end:<num> name:<func> [dry_run:<true|false>]`

*Allowed tools:* `read_file`, `write_file`, `edit_file`, `shell`

*Constraints:*
- No file deletion
- No new dependencies
- No changes to `.env` or key files
- Extracted function must have docstring
- Must run pytest. Rollback on failure

*Args:*
Arg | Required | Description | Example
`file:` | Yes | Target file | `file:src/billing.py`
`start:` | Yes | Start line of block | `start:20`
`end:` | Yes | End line of block | `end:35`
`name:` | Yes | New function name | `name:calc_tax`
`dry_run:` | No | Preview only | `dry_run:true`
*Example:*
/skill refactor_extract_function file:src/billing.py start:20 end:35 name:calc_tax dry_run:false
Extracts lines 20-35 into `def calc_tax(...):`, replaces original with call, writes `tests/test_billing_calc_tax.py`.

*Failure modes:*
❌ Missing required arguments. Need file:, start:, end:, name:
❌ start: 35 >= end: 20. Invalid range.
[REFACTOR] Tests failed after extraction. Rolled back.
---

## 3. doc_sync

*Purpose:* Synchronize docstrings and README sections with actual code signatures using AST + LLM.

*Location:* `skills/doc_sync/`

*Trigger:* `/skill doc_sync code:<path> docs:<path> [target:function|class|module|readme] [dry_run:<true|false>]`

*Allowed tools:* `read_file`, `write_file`, `edit_file`, `list_files`

*Constraints:*
- No file deletion
- No new dependencies
- No changes to `.env` or key files
- Minimal diffs only. Won’t rewrite entire files unless `docs:<path>` is new

*Args:*
Arg | Required | Description | Example
`code:` | Yes | Source code file | `code:src/api.py`
`docs:` | Yes | Doc file to update | `docs:README.md`
`target:` | No | Scope: function/class/module/readme. Default: module | `target:readme`
`dry_run:` | No | Show diff only | `dry_run:true`
*Example:*
/skill doc_sync code:src/api.py docs:src/api.py target:module dry_run:true
Shows diff updating docstring params to match `def login(user, pwd, remember=False)`
/skill doc_sync code:src/api.py docs:README.md target:readme dry_run:false
Updates README code examples to match current API.

*Failure modes:*
❌ Missing required arguments. Usage: /skill doc_sync code:<path> docs:<path>
[DOC_SYNC] No functions found in src/api.py
---

## 4. generate_playbook

*Purpose:* LLM-generate a reasoning playbook Markdown file with YAML front-matter for PlaybookRegistry.

*Location:* `skills/generate_playbook/`

*Trigger:* `/skill generate_playbook category:<name> | description:<text> | keywords:<csv> | dry_run:<true|false>`

*Allowed tools:* `list_files`, `read_file`, `write_file`, `edit_file`

*Constraints:*
- Write-only. No code execution
- Output path must be `playbooks/<category>/*.md` only
- Must include valid YAML: `name`, `description`, `keywords`, `triggers`
- No network access

*Args:*
Arg | Required | Description | Example
`category:` | Yes | Playbook category dir | `category:testing`
`description:` | Yes | One-line summary | `description:pytest guide`
`keywords:` | No | CSV for search. Auto-generated if omitted | `keywords:test,pytest,assert`
`dry_run:` | No | Preview only | `dry_run:true`
*Example:*
/skill generate_playbook category:testing | description:mutation testing guide | keywords:mutation,mutant | dry_run:false
Creates `playbooks/testing/mutation_testing_guide.md` with YAML front-matter + sections: When to use, Steps, Examples, Pitfalls.

*Failure modes:*
❌ Playbook already exists: playbooks/testing/mutation_testing_guide.md
❌ Generated playbook invalid: Missing sections: ['## Steps']
❌ Category cannot contain path separators.
---

## 5. create_skill_py

*Purpose:* Meta-skill: compile `SKILL.md` spec → `skill.py` implementation. Deterministic/LLM/hybrid modes.

*Location:* `skills/create_skill_py/`

*Trigger:* `/skill create_skill_py <skill-name> [--overwrite] [--llm] [--dry_run]`

*Allowed tools:* `list_files`, `read_file`, `write_file`

*Constraints:*
- Workspace-only. Must stay in `./skills/<skill-name>/`
- `prevents-overwriting: true` unless `--overwrite`
- Must validate generated code with `validate_skill_py` before writing

*Args:*
Arg | Required | Description | Example
`<skill-name>` | Yes | Directory under `./skills/` | `bug_fix`
`--overwrite` | No | Replace existing `skill.py` | `--overwrite`
`--llm` | No | Force LLM mode | `--llm`
`--dry_run` | No | Preview code only | `--dry_run`
*Example:*
/skill create_skill_py doc_sync --dry_run
Shows generated `skill.py` code without writing.
/skill create_skill_py bug_fix --overwrite
Regenerates `./skills/bug_fix/skill.py` from `SKILL.md`. Mode: hybrid by default.

*Failure modes:*
❌ No SKILL.md found in ./skills/bug_fix
❌ skill.py already exists. Use --overwrite to regenerate.
❌ Generated skill.py failed validation: Missing run() method
❌ Invalid YAML in SKILL.md: execution_mode must be deterministic|llm|hybrid
---

## 6. scaffold_project

*Purpose:* Bootstrap new Python project: `pyproject.toml`, `src/` layout, `tests/`, `.gitignore`.

*Location:* `skills/scaffold_project/`

*Trigger:* `/skill scaffold_project name:<app_name> [type:lib|app] [dry_run:<true|false>]`

*Allowed tools:* `write_file`, `list_files`

*Constraints:*
- Write-only
- No overwriting existing files unless `force:true`
- Must stay under workspace root

*Args:*
Arg | Required | Description | Example
`name:` | Yes | Project/package name | `name:myapp`
`type:` | No | `lib` or `app`. Default: `lib` | `type:app`
`dry_run:` | No | List files to create | `dry_run:true`
*Example:*
/skill scaffold_project name:myapp type:lib dry_run:false
Creates:
myapp/
├── pyproject.toml
├── src/myapp/__init__.py
├── tests/test_myapp.py
└── .gitignore
*Failure modes:*
❌ Project name 'myapp' already exists
❌ Invalid type 'web'. Must be: lib|app
---

## 7. hello

*Purpose:* Trivial example skill that echoes its input. Verifies the skills layer is wired up without doing anything risky.

*Location:* `skills/hello/`

*Trigger:* `/skill hello [message]`

*Allowed tools:* none

*Constraints:*
- No side effects — echoes the request back, nothing else

*Example:*
```
/skill hello world
Output: [HELLO SKILL] Got request: '/skill hello world'
```

---

## 8. listallpy

*Purpose:* List all `*.py` files in the workspace.

*Location:* `skills/listallpy/`

*Trigger:* `/skill listallpy`

*Allowed tools:* `list_files` (per `SKILL.md`)

*Constraints:*
- Workspace only
- No network access

*Example:*
```
/skill listallpy
Output: app.py
        csv_summary.py
        hello.py
```

*Note:* generated live via `/skill generate_skill` — see `docs/ISSUES.md` ISS-011 for known
output-quality gaps in the `generate_skill` path (not specific to this skill).

---

## Deprecated Skills

### generate_skill
*Status:* Deprecated. Use `create_skill_py` instead.  
*Reason:* `generate_skill` was LLM-only and wrote directly to root. `create_skill_py` enforces SKILL.md spec + validation.

---

## Writing a New Skill

1. Create dir: `skills/<skill_name>/`
2. Add `SKILL.md` with YAML front-matter: `name`, `description`, `trigger`, `allowed_tools`, `constraints`, `status: proposed`
3. Add `skill.py` subclassing `Skill` with `name()`, `description()`, `run()`
4. Use only `context.agent_tools` for I/O. ADR-016.
5. Set `status: approved` after code review
6. Run `/clear` to reload SkillRegistry

See [Skills Architecture](../README_Skills.md) for ADR-010 approval gate and reasoning vs execution layer.

