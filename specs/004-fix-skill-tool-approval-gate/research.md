# Phase 0 Research: Fix Skill/Tool Approval Gate

No `NEEDS CLARIFICATION` markers remained — the prior planning conversation (including a
live demonstration of the actual bug against the real, pre-fix code) already resolved every
open design question, including the two explicit trade-off decisions the user signed off on.

## Decision: Content-hash approval ledger, not a status-field-only gate

**Decision**: A new tracked file, `skills/.approvals.json`, records `{skill_name: {sha256,
timestamp}}` for each approved skill. `SkillRegistry.load()`/`reload_skill()` only execute
`skill.py` when `status == "approved"` **and** the ledger's recorded hash matches the
current file's hash.

**Rationale**: Live-confirmed during planning: a `status: proposed` skill's module-level
code executed unconditionally at `SkillRegistry.load()` — approval status was checked only
for a log message, never to gate execution. A status-only gate (just checking
`status == "approved"` before `exec_module`) would close that specific bug, but leaves a
real tamper vector open: someone can edit `skill.py` to something unsafe and flip
`status: approved` in the same commit, and the load path has no way to know the reviewed
content and the current content differ. The hash ledger closes this — it's the "explicit
trusted activation record outside the artifact being approved" the audit specifically asked
for — and incidentally gives the separate M-01 finding (no immutable approval audit trail)
a real, load-bearing fix rather than just a log entry nobody checks.

**Alternatives considered**:
- *Status-only gate* — simpler, smaller diff, fully closes the concretely demonstrated bug
  (code no longer runs before any approval at all). Rejected in favor of the ledger after
  discussing the trade-off directly with the user — they preferred the more complete fix
  given its cost was modest (hash a file, compare two strings) relative to the value.
- *A full digital-signature scheme* (e.g. requiring a cryptographic signature over
  `skill.py`, verified against a trusted key) — rejected as disproportionate: this is a
  local, single-operator development tool, not a multi-party trust system; a content hash
  tied to an explicit `/approve` action already satisfies "can't silently bundle a code
  change with its own approval," without introducing key management.

## Decision: One-time auto-seed for the 8 already-approved skills

**Decision**: On registry load, any skill with `status: approved` that has no ledger entry
gets one written automatically, with an explicit "seed event, not a review" log line — not
silently indistinguishable from a real `/approve` action.

**Rationale**: Under a strict ledger-required rule, the 8 skills already `status: approved`
in this repo (`hello`, `generate_skill`, `scaffold_project`, `bug_fix`,
`generate_playbook`, `doc_sync`, `create_skill_py`, `refactor_extract_function`) would stop
loading the moment the ledger check goes live, since none has an entry yet. The user
explicitly confirmed they want zero disruption to these — a one-time, automatic seed,
clearly logged as such, is the agreed resolution. This trusts their current content by
fiat, not a real re-review; that's a conscious, visible trade-off, not a silent one.

**Alternatives considered**:
- *Require explicit re-approval of all 8* — the more rigorous option (actually re-reviewed,
  not just recognized), explicitly offered to and declined by the user, since it would take
  8 currently-working skills offline until manually re-approved one at a time — a real
  regression the user didn't want to accept for this fix.

## Decision: Dynamic tools — `ENABLE_DYNAMIC_TOOLS` (default false) plus static validation

**Decision**: New `ENABLE_DYNAMIC_TOOLS` env var, same truthy-string-parsing pattern as
`ENABLE_SHELL_TOOL`, gates whether `load_dynamic_tools()` is even called (in `main.py` and
`agent.py`'s `_reload_dynamic_tools()`). Independent of that gate, `load_dynamic_tools()`
itself now runs the same forbidden-pattern/AST check `validator.py` already does for
skills, before `exec_module`, skipping (not crashing on) any file that fails.

**Rationale**: Dynamic tools have zero approval concept today — any file dropped into
`dynamic_tools/` auto-executes, worse than skills' bug (which at least had a status field
being ignored). The audit's own explicit interim recommendation is "disable
runtime-generated tools... until [isolated execution] exists." `ENABLE_SHELL_TOOL` is the
established, already-approved precedent for exactly this shape of decision in this repo
(ISS-002) — same structure: genuinely risky always-on capability → explicit opt-in, default
false, honest about what it does and doesn't guarantee. The user confirmed this explicitly,
accepting that their 5 existing local `dynamic_tools/*.py` files stop auto-loading until the
var is set once — the same one-time-opt-in cost they already accepted for shell.

**Alternatives considered**:
- *Static validation only, keep auto-loading enabled* — presented directly to the user as
  the zero-disruption alternative and declined, since it doesn't close the core gap this
  issue is about (code with no known-bad pattern still executes with zero human approval,
  ever) — only narrows to *known* bad patterns, which is meaningfully weaker than requiring
  an explicit, human, opt-in decision.

## Decision: `FORBIDDEN_PATTERNS` shared from `validator.py`, not duplicated

**Decision**: `py_mono/tools/tool_loader.py` and `py_mono/tools/create_tool.py` import
`FORBIDDEN_PATTERNS` (and the `ast`-based structural checks needed) from
`py_mono/skill/validator.py` rather than maintaining a second copy of the pattern list.

**Rationale**: `validator.py`'s `validate_skill_py` is already genuinely non-executing
(confirmed: no `exec`/`eval`/`exec_module` anywhere in that module) and already covers the
exact threat class (dangerous imports/calls at module scope). A second, separately
maintained list for dynamic tools would drift from the skills list over time — a classic
source of exactly the kind of silent gap this fix exists to close. Reusing the canonical
source keeps both code paths covered by one list going forward.

**Alternatives considered**:
- *A separate, dynamic-tool-specific validator module* — rejected: dynamic tools and
  skills share the same underlying threat model (arbitrary Python executing at discovery
  time); a second bespoke implementation would be pure duplication for no benefit.

## Decision: ADR-013 correction in place, not a new ADR

**Decision**: Add an "Implementation Notes: corrected 2026-08-03" section to the existing
`docs/adr/ADR-013-*.md` (Skill Approval and Chaining Policy) rather than authoring a new ADR.

**Rationale**: ADR-013 already states proposed skills have "Execution Allowed? No" — the
bug fixed here is a gap between that stated policy and the actual code, not a new policy
decision. Mirrors exactly how ISS-002 corrected ADR-001 in place (Proposed → Accepted, with
a dated correction note) rather than writing a new ADR for the same underlying concern.

**Alternatives considered**:
- *A new ADR specifically for the approval-ledger mechanism* — rejected: the ledger is an
  implementation detail enforcing ADR-013's existing, already-correct policy intent, not a
  new architectural decision requiring its own record.
