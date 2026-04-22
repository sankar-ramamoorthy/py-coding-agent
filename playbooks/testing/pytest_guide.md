---
name: pytesting
description: Standards and workflow for writing, running, and fixing pytest suites
keywords: [test, pytest, unittest, coverage, assert, fixture, mock, tdd, regression, test_]
triggers: ["write tests", "add test", "coverage", "test this", "pytest fails", "no tests"]
category: quality
priority: medium
---

# Pytest Testing Playbook

## When to use
Activate when the user mentions:
- Writing new tests for existing code
- `pytest` failures that aren't crashes — assertion errors, wrong output
- Coverage gaps or `no tests` for a module
- TDD: “test this behavior before I implement it”

Do NOT use for debugging runtime crashes. Use `debugging` playbook for that.

## Steps: Test-Driven Workflow

### Step 0: Scope Check
Respond with `action: answer` and confirm:
1. **Target**: What file/function/module needs tests? `read_file` to see it first.
2. **Behavior**: What are the 2-3 critical behaviors to verify? Ask if unclear.
3. **Framework**: Confirm pytest. If `unittest` detected, ask to migrate.

DO NOT write test code until scope is locked. No guessing.

### Step 1: Inspect & Plan
1. `read_file` on target module to understand public API.
2. `shell: ls tests/` to see existing test structure. Follow it.
3. Plan test names: `test_<function>_<condition>_<expected>`. Example: `test_login_invalid_password_returns_401`

Output plan via `action: answer` before writing.

### Step 2: Write Tests
Call `write_file` or `test_writer` skill to create `tests/test_<module>.py`.

**Standards:**

import pytest
from my_module import function_under_test

def test_function_happy_path():
    result = function_under_test(valid_input)
    assert result == expected

def test_function_raises_on_bad_input():
    with pytest.raises(ValueError):
        function_under_test(None)

@pytest.fixture
def db_session():
    # setup/teardown here
    yield session
Rules: One assert per test when possible. Use fixtures for setup. No `print`, use `assert`.

### Step 3: Run & Iterate
1. `shell: pytest -v tests/test_<module>.py` 
2. If failures: read output, fix code OR fix test. If code is wrong, switch to `debugging` playbook.
3. Repeat until green.

### Step 4: Coverage Gate
1. `shell: pytest --cov=my_module --cov-report=term-missing`
2. If coverage <80% on new code, identify missing lines via `term-missing` output.
3. Add tests for those branches. Goal: 100% on new code, 80%+ overall.

### Step 5: Regression Check
`shell: pytest` full suite. If unrelated tests broke, your change has side effects. Fix before proceeding.

## Examples

*Input*: "write tests for auth.py"
*Step 0*: `read_file path=auth.py` → see `login()`, `verify_password()`
*Step 1*: Answer: "I'll test login success, login bad password, login missing user. OK?"
*Step 2*: `write_file path=tests/test_auth.py` with 3 tests
*Step 3*: `shell: pytest -v tests/test_auth.py`
*Step 4*: `shell: pytest --cov=auth --cov-report=term-missing`

## Pitfalls

1. *Testing implementation, not behavior*: Don't assert internal variables. Test inputs → outputs.
2. *Flaky tests*: No `time.sleep`, no network, no random. Use `freezegun` for dates, `responses` for HTTP.
3. *Fixture scope abuse*: `scope="session"` for DB only. Default `function` prevents state leak.
4. *Ignoring warnings*: `pytest -W error` to make deprecation warnings fail CI.
5. *Writing tests after bugs*: If you found a bug, write the failing test FIRST, then fix. That’s the regression test.

## Anti-patterns
- Do NOT use `unittest.TestCase`. Use pytest functions.
- Do NOT mock everything. Mock IO boundaries only: DB, network, filesystem.
- Do NOT skip tests with `@pytest.mark.skip`. Fix or delete.
- Do NOT output test code in chat. Call `write_file` or `test_writer` skill.

## Integration with other playbooks
- If `pytest` fails with `ImportError` or `NameError`: hand off to `debugging` playbook.
- If tests pass but coverage low: stay in this playbook, Step 4.
- If new feature: `software-design` playbook should have created tests already. This playbook backfills gaps.

