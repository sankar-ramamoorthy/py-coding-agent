---
name: mylistpythonfiles
description: List all python files in current folder
status: approved
allowed_tools: [list_files]
constraints: [read-only, workspace only, no network]
---

# mylistpythonfiles

Lists all Python source code files (files ending with `.py`) in the current working directory by name only.

## Usage

```
/skill mylistpythonfiles
```

## Expected Output

A newline-separated list of Python file names in the current directory.

## Constraints

- Only shows files in the immediate working directory (no recursion)
- Shows only file names, no metadata or file contents
- Does not execute or modify any files