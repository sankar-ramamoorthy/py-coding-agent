---
name: software-design
description: Guides API design workflow from requirements to scaffold
keywords: [build, create, api, flask, fastapi, backend, jwt, rest, scaffold, design]
triggers: ["build me", "create api", "new project"]
---

# Software Design Playbook (Minimal)

## When to use

* User asks to *build, create, make, or write* a program/system
* User describes a feature to implement
* User requests a script, app, API, or tool

---

## Core principle

**Never write code before understanding requirements.**
Ask at least one clarifying question unless the task is trivial.

---

## Strategy

### Step 1: Understand the goal

Before writing code, identify:

* What problem is being solved?
* Who uses it and how?
* What does success look like?

If unclear → ask 1–3 focused questions.

---

### Step 2: Ask focused clarifying questions

Ask only the most impactful questions (2–3 max):

* Interface: CLI, API, library, web app?
* Inputs/outputs: files, stdin, HTTP, DB?
* Constraints: language, libraries, environment?
* Tests: required or not?
* Scale: quick script or maintainable system?

Avoid over-questioning.

---

### Step 3: Confirm the design

Summarize before building:

```
Here's what I'll build:
- Goal: [1–2 sentences]
- Interface: [type]
- Inputs/Outputs: [brief]
- Files: [list]
- Dependencies: [list]
- Tests: yes/no
- Success criteria:
  - [what defines “done”]

Proceed?
```

If user says “just do it” → skip confirmation and proceed with best assumptions.

---

### Step 4: Write requirements.md

Create `workspace/requirements.md` with:

* Problem statement
* Assumptions (explicit — don’t hide guesses)
* Inputs/outputs
* Success criteria
* Brief approach

If file exists → read and update it.

---

### Step 5: Build

**Single-file task**

* Write the file directly
* Skip scaffolding

**Multi-file system**

* Use `scaffold-project`
* Then implement

---

### Step 6: Implement simply first

* Build the minimal working version (happy path)
* Add tests if requested
* Avoid over-engineering

---

## Heuristics

* “Just do it” → document assumptions, then proceed

* Unknown choices (DB, auth, etc.) → pick a simple default and document it

* Prefer:

  * SQLite for storage
  * `pytest` for Python tests

* Don’t create many files unless necessary

* Don’t introduce frameworks unless justified

---

## Failure handling

* If something fails (scaffold, file write, tests):

  * Stop
  * Report clearly what failed
  * Suggest next step

Do not continue blindly after errors.

---

## Anti-patterns to avoid

* Writing code before confirming understanding
* Asking too many questions
* Making hidden assumptions
* Overbuilding (frameworks, configs, abstractions too early)
* Generating multi-file projects without a requirements.md

---

## Examples

### Simple request

> “Write a script that summarizes a CSV”

* Ask 1–2 questions
* Write single file
* Done

---

### Complex request

> “Build a REST API with auth”

* Ask key questions (auth method, DB)
* Confirm design
* Write requirements.md
* Scaffold
* Implement

---

## Minimal checklist before coding

* [ ] Goal is clear
* [ ] Key questions answered (or assumptions made)
* [ ] requirements.md written (for non-trivial tasks)
* [ ] Success criteria defined

