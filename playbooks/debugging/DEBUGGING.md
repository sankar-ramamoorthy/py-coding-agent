---
name: debugging
description: Systematic workflow for diagnosing test failures, runtime errors, and regressions
keywords: [debug, fix, error, failing, broken, stacktrace, traceback, pytest, exception, bug, regression]
triggers: ["test failed", "getting error", "not working", "debug this", "why is this breaking"]
category: diagnostic
priority: high
---

# Debugging Playbook

## When to use
This playbook activates when the user reports:
- Failing `pytest` or test suite
- Runtime exceptions / stack traces
- Unexpected behavior vs requirements
- CI pipeline failures

## Strategy: Scientific Debugging Loop

### Step 0: Gate Check
If no error message, logs, or failing test output provided, respond with `action: answer` and ask for:
1. Full stack trace or error message
2. Command that triggered it
3. Recent changes since last green build

DO NOT proceed to tools/skills until you have reproduction info.

### Step 1: Reproduce
Call `shell` tool: run the exact command that fails. Capture stdout/stderr.
Goal: Get deterministic failure in agent environment.

### Step 2: Localize
1. Read the stack trace top-down. The last line in YOUR code is usually the culprit.
2. Use `read_file` on the failing file + line numbers around the error.
3. Use `git diff` via `shell` to see recent changes to that file.

### Step 3: Hypothesize
Based on trace + diff, form ONE hypothesis. Example: "Null value from API due to schema change in commit abc123"

Respond with `action: answer` stating the hypothesis and proposed minimal fix.

### Step 4: Validate
1. If hypothesis requires code change, call `bug_fix` skill with targeted prompt.
2. `bug_fix` must run `pytest` and fail if tests don't pass.
3. If no `bug_fix` skill or fix is <5 lines, use `write_file` via a `hotfix` skill.

### Step 5: Regression Proof
Ensure `pytest` adds a test that would have caught this. If tests pass, summary includes: root cause, fix, regression test added.

## Heuristics
- **Stack traces**: Your code is between `File "/workspace/...` lines. Vendor code is noise.
- **Recent diffs**: 80% of bugs are in last 3 commits. Check `git log -p -3`.
- **Minimal fixes**: If fix >20 lines, you misunderstood the problem. Stop and re-hypothesize.
- **Never guess**: If you can't reproduce, say so. Don't speculate.

## Anti-patterns
- Do NOT run `refactor` or `scaffold_project` during debugging. Fix first.
- Do NOT apologize or add verbose explanations. State cause → fix → test.
- Do NOT output code in chat. Write it via skills/tools.

## Examples

Input: `pytest tests/test_api.py::test_login -v` fails with `AssertionError: 401 != 200`
Step 1: Run `shell: pytest tests/test_api.py::test_login -v` to confirm
Step 2: Read trace, see `auth.py:43` in `verify_password`
Step 3: `git diff HEAD~1 auth.py` shows password hash algo changed
Step 4: Call `bug_fix` skill: "Fix verify_password to use bcrypt, not sha256. Add test for legacy hash migration."