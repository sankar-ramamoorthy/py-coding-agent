# Software Design Playbook

## When to use
- User asks to "build", "create", "make", or "write" a program or system
- User describes a feature they want implemented
- User says "I need a script/app/API/tool that..."

## Core principle
**Never write files before understanding requirements.**
Even if the request seems clear, ask at least one clarifying question.
A short conversation now prevents a full rewrite later.

## Strategy

### Step 1: Understand the goal
Before writing a single line of code, identify:
- What problem does this solve?
- Who uses it and how?
- What does success look like?

### Step 2: Ask focused clarifying questions
Ask the most important questions only. Do not interrogate the user.
Good questions to ask (pick the most relevant 2-3):

- **Interface**: CLI script, REST API, library, or web app?
- **Data**: What are the inputs and outputs? Files, stdin, HTTP, database?
- **Dependencies**: Any specific libraries required or preferred?
- **Tests**: Should I include a test suite?
- **Scale**: Is this a one-off script or a maintainable system?

### Step 3: Confirm the design
Before scaffolding, summarize your understanding:
```
Here's what I'll build:
- [brief description]
- Files: [list]
- Dependencies: [list]
- Tests: yes/no

Shall I proceed?
```

### Step 4: Write requirements.md
Once confirmed, write the requirements to `workspace/requirements.md` first.
This gives you and the user a shared reference and persists across sessions.

### Step 5: Scaffold
Use the `scaffold-project` skill to generate the files.
Do not write files directly via write_file one by one unless scaffolding a single file.

## Heuristics

- If the user says "just do it" or "don't ask questions" — write `requirements.md` 
  with your best interpretation, show it, then proceed
- For single-file requests ("write a script that..."), skip the full workflow and
  write directly — no need for scaffold-project
- For multi-file systems (APIs, packages, apps), always go through requirements.md
- If you are unsure about any constraint, ask — guessing the wrong database or
  auth method means rewriting everything

## Examples

### Simple request (single file — write directly)
```
User: "Write a script that reads a CSV and prints a summary"
→ Ask: any specific columns? output format?
→ Write: workspace/csv_summary.py
→ Run: python csv_summary.py (if test data available)
```

### Complex request (multi-file — use scaffold-project)
```
User: "Build me a Flask REST API with user auth"
→ Ask: JWT or session? SQLite or Postgres? tests?
→ Write: workspace/requirements.md
→ Skill: scaffold-project
→ Run: pytest
```

## Anti-patterns to avoid
- Writing 10 files and then asking "does this look right?" — too late
- Making assumptions about database, auth, or framework without asking
- Generating code without any tests when the user didn't say "no tests"
- Ignoring an existing `workspace/requirements.md` — always read it first