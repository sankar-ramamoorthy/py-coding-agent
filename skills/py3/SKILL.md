---
name: py3
description: list all python programs in "."
status: approved
allowed_tools: [list_files]
constraints: [read-only, workspace only, no network, only lists .py files]
---

# py3

This skill scans the current workspace directory to identify and list all Python programs with a `.py` file extension using the `list_files` tool.

## Usage

```
/skill py3
```

## Expected Output

Structured JSON list of Python files in the current directory, filtered by `.py` extension.

## Constraints

- Only lists files with `.py` extension
- Operates in current workspace directory
- Does not execute or modify files
- No network operations allowed