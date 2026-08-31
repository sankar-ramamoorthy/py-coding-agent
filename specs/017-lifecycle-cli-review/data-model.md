# Data Model: Lifecycle CLI Review Polish

## SkillReview

- `skill_name`: Requested skill name.
- `skill_path`: Skill directory.
- `candidate_path`: Candidate directory when present.
- `has_candidate`: Whether both candidate artifacts are present.
- `report`: Parsed lifecycle report when available.
- `markdown_fallback`: Markdown report text when JSON is unavailable.

## ReviewSummary

- `status`: Lifecycle report status.
- `mode`: Lifecycle mode.
- `stages`: Ordered stage results.
- `smoke_test`: Smoke-test summary.
- `diffs`: Diff summary per artifact.
- `next_steps`: Suggested review and approval steps.

## ApprovalOutcome

- `skill_name`: Approved or rejected skill.
- `candidate_promoted`: Whether a `.candidate` was promoted.
- `report_path`: Retained lifecycle report path when available.
- `message`: Human-readable outcome.
