# Data Model: Skill Regeneration Diff

## ApprovedBaseline

Represents the last approved skill artifacts available for comparison.

**Fields**:
- `skill_name`
- `skill_md_content`
- `skill_py_content`
- `approved_hash`
- `source`: where the baseline was recovered from

**Rules**:
- The baseline must correspond to the approval ledger hash when possible.
- If no reliable baseline exists, the diff result must report that explicitly.

## RegeneratedSkillCandidate

Represents regenerated artifacts after the `ISS-015` lifecycle passes.

**Fields**:
- `skill_name`
- `skill_md_content`
- `skill_py_content`
- `lifecycle_result`
- `status`: proposed

**Rules**:
- Must remain proposed.
- Must not update the approval ledger.

## ArtifactDiff

Represents the user-visible comparison.

**Fields**:
- `artifact`: `SKILL.md` or `skill.py`
- `changed`: boolean
- `diff_text`: rendered diff or no-change message
- `baseline_available`: boolean

**Rules**:
- Diffs for `SKILL.md` and `skill.py` must be distinguishable.
- Missing baselines must not be reported as no-change.
