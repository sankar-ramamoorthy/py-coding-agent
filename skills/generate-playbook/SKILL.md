---
name: generate-playbook
description: Generate a new reasoning playbook (Markdown) using the LLM
status: approved
allowed_tools: [read-file,write-file]
constraints: write-only, playbooks directory only, no code execution
---

# generate-playbook

Creates a Markdown playbook that guides reasoning (not execution).

## Usage

/skill generate-playbook <category> | <description>

Example:
/skill generate-playbook testing | Guide for writing pytest test suites

## Expected Output

A new Markdown file under playbooks/<category>/ with structured guidance.

## Constraints

- Must not generate executable code
- Must write only inside playbooks/
- Output must be valid Markdown