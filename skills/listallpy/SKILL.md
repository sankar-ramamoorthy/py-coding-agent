---
name: listallpy
description: list all python programs in current directory
status: approved
allowed_tools: [list_files]
---

# listallpy

Lists every Python file (`.py`) present in the current workspace directory and returns them in a clean, human-readable format.

## Usage

````

/skill listallpy

````

## Expected Output

A simple list of Python filenames, one per line, found in the current directory.

## Constraints

- Only lists files in the immediate directory (non-recursive)
- No file contents are read or modified
- No network access required