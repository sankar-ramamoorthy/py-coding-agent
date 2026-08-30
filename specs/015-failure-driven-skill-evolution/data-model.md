# Data Model: Failure-Driven Skill Evolution

## SkillFailureContext

Represents failure evidence used to propose a revision.

**Fields**:
- `skill_name`
- `request`
- `failure_reason`
- `provider`
- `model`
- `timestamp`

**Rules**:
- Must identify the failed skill.
- Must include enough failure detail to inform generation.
- If unavailable, evolution must stop with a clear explanation.

## EvolutionProposal

Represents generated revised artifacts based on failure context.

**Fields**:
- `skill_name`
- `failure_context`
- `skill_md_content`
- `skill_py_content`
- `lifecycle_result`
- `status`: proposed

**Rules**:
- Must re-enter the `ISS-015` lifecycle.
- Must not replace approved behavior until explicit approval.

## EvolutionOutcome

Represents the user-visible result.

**Fields**:
- `status`: proposed, failed, or unavailable
- `message`
- `lifecycle_result`
- `next_step`

**Rules**:
- Failed lifecycle stages block proposal.
- Missing failure context blocks generation.
