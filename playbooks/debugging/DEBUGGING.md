# Debugging Playbook

## When to use
- Tests are failing
- Runtime errors
- Unexpected behavior

## Strategy
1. Reproduce the issue
2. Narrow the scope
3. Inspect recent changes
4. Form hypothesis
5. Validate with tests

## Heuristics
- Check stack trace first
- Focus on recent diffs
- Prefer minimal fixes

## Examples
Input: failing pytest with stack trace
Output: identify failing line, propose fix, add regression test