# Data Model: Fix pre-existing test failures

No new entities. The only existing persisted structure touched is `skills/.approvals.json`
(the approval ledger), whose schema is unchanged — only the `sha256` field's computation
changed (normalized line endings before hashing), not its shape:

```json
{
  "<skill_name>": {
    "sha256": "<hex digest of skill.py content, \\r\\n normalized to \\n>",
    "recorded_at": "<ISO 8601 timestamp>",
    "seeded": "<bool — true if migrated from a pre-ledger approved status, false if a genuine /approve>"
  }
}
```

All 9 existing entries were regenerated in place using the fixed `hash_file()`; no entries were
added or removed, and `recorded_at`/`seeded` metadata was preserved unchanged.
