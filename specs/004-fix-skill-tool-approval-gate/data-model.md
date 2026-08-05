# Phase 1 Data Model: Fix Skill/Tool Approval Gate

## Approval ledger entry (`skills/.approvals.json`)

A JSON object mapping skill name → entry:

```json
{
  "hello": {
    "sha256": "a1b2c3...",
    "recorded_at": "2026-08-03T00:00:00Z",
    "seeded": false
  }
}
```

| Field | Type | Meaning |
|---|---|---|
| `sha256` | string | Hex digest of `skill.py`'s content at the moment this entry was written |
| `recorded_at` | string (ISO 8601) | When this entry was written |
| `seeded` | boolean | `true` if this entry was written by the one-time auto-seed (existing already-approved skill, not a genuine `/approve` action), `false` if written by a real approval |

## Skill load-gating rule (not a persisted entity — evaluated at `load()`/`reload_skill()` time)

| `status` (SKILL.md) | Ledger entry exists? | Hash matches current `skill.py`? | Result |
|---|---|---|---|
| `approved` | No | — | Not loaded (until a ledger entry exists — see auto-seed) |
| `approved` | Yes | Yes | Loaded, `exec_module` runs |
| `approved` | Yes | No (file changed since approval) | Not loaded — reverted, requires re-approval |
| `proposed` (or anything else) | (any) | (any) | Not loaded, regardless of ledger state |

Metadata (name, description, status) is always parsed and available via `list_skills()`
regardless of load state — only `exec_module` and `Skill` instantiation are gated.

## One-time auto-seed (a write, not a read rule — happens during `load()`)

For each skill where `status == "approved"` and no ledger entry exists: compute the current
`skill.py`'s hash, write a ledger entry with `seeded: true`, log an explicit "auto-seeded,
not reviewed" message, then proceed to load it (hash now matches by construction). Runs
once per skill — after the first seed, subsequent loads follow the normal matching rule.

## `/approve` action (state transition)

```text
[skill.py content C, SKILL.md status: proposed, no/stale ledger entry]
        │  operator runs /approve <name>
        ▼
[validate_skill_py(C) called]
        │
        ├─ invalid ──────────────► [rejected: SKILL.md unchanged, ledger unchanged,
        │                            error message returned, nothing executed]
        │
        └─ valid
              │
              ▼
[SKILL.md status: approved, ledger entry {sha256(C), now, seeded: false} written]
        │
        ▼
[reload_skill(name) called → hash matches → exec_module runs]
```

If `skill.py`'s content later changes to `C'` (`sha256(C') != sha256(C)`), the next
`load()`/`reload_skill()` finds a hash mismatch and reverts to not-loaded — same diagram,
re-entering at "operator runs /approve" to regain a matching ledger entry.

## Dynamic tool gating (not persisted — evaluated at call sites)

| `ENABLE_DYNAMIC_TOOLS` | `load_dynamic_tools()` called at all? | Per-file static validation |
|---|---|---|
| `false` (default) | No — `main()` and `_reload_dynamic_tools()` skip the call entirely | N/A |
| `true` | Yes | Each file's text is checked against the shared `FORBIDDEN_PATTERNS`/AST rules from `validator.py` before `exec_module`; failing files are skipped (logged), not raised |

## `create_tool()` gating (evaluated before any write)

| Input `code` | Validation result | Outcome |
|---|---|---|
| Contains a forbidden pattern or fails to parse | Invalid | Nothing written to disk; error string returned |
| Clean | Valid | `wrapped_code` written to `dynamic_tools/{name}.py`, exactly as today |
