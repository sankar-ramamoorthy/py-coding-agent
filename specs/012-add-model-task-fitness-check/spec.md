# Feature Specification: Model/task fitness check

**Feature Branch**: `add-model-task-fitness-check`

**Created**: 2026-08-05

**Status**: Draft (documents completed, verified work)

**Input**: User description: "Add ISS-014 — warn before a heavy generation call if the
configured model looks like a poor fit for structured output, using the ISS-013 telemetry log
as the data source. Productizes the ISS-009/ISS-011 lesson (thinking models reasoning
verbosely/unreliably on template-filling tasks). Depends on ISS-013 landing first. See
docs/ROADMAP_PLAN.md Milestone 6 and docs/ISSUES.md ISS-014."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get warned when a model/task combination has a real failure history (Priority: P1)

An operator runs a skill using a provider/model combination that has recently failed more often
than not for that exact skill. Instead of discovering this the hard way each time, the result
carries a visible warning suggesting they switch providers/models.

**Why this priority**: This is the concrete, evidence-based feature named in Milestone 6 —
"the clearest bug-we-hit-to-feature-that-prevents-the-next-one line" from this session, directly
motivated by two real bugs (`ISS-009`, `ISS-011`) both involving a poor-fit model.

**Independent Test**: Seed the telemetry log with a majority-failing history for a (skill,
provider, model) combination, run that skill again, and confirm the result carries a warning.

**Acceptance Scenarios**:

1. **Given** a (skill, provider, model) combination has failed at least half of its most recent
   runs (with at least a minimum sample size recorded), **When** that skill runs again, **Then**
   the result is prefixed with a warning naming the skill, provider, model, and observed failure
   count.
2. **Given** a (skill, provider, model) combination has a healthy success rate, **When** that
   skill runs, **Then** no warning is added and the result is unchanged.
3. **Given** a (skill, provider, model) combination has fewer recorded runs than the minimum
   sample size, **When** that skill runs, **Then** no warning is added (avoids a false positive
   from a single failure).
4. **Given** a skill run itself fails, **When** the exception propagates, **Then** no fitness
   warning is attached (there is no successful result to attach it to).

### Edge Cases

- Does an old run of failures permanently flag a model even after a fix lands? No — only the
  most recent window of runs for that exact combination is considered, so the flag clears once
  enough recent runs succeed.
- Does a failure for a *different* skill, provider, or model pollute this check? No — matching
  is exact on all three fields; telemetry for unrelated combinations is ignored.
- What if the telemetry log doesn't exist yet (fresh install)? No warning — the check requires
  actual recorded history and degrades to "no opinion" when none exists, never erroring.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST warn when a (skill, provider, model) combination's most recent
  runs show a failure rate at or above a defined threshold.
- **FR-002**: The system MUST NOT warn when there are fewer recorded runs for that exact
  combination than a defined minimum sample size.
- **FR-003**: The check MUST use only telemetry for the exact (skill, provider, model)
  combination being run — no cross-contamination from other skills, providers, or models.
- **FR-004**: The check MUST consider only a recent window of runs, not full history, so
  fitness improves once a fixed model/provider starts succeeding again.
- **FR-005**: A warning MUST be non-blocking — it never prevents the skill from running, only
  adds visibility to the result.
- **FR-006**: A warning MUST NOT be attached to a failed run (there is no successful result to
  prepend it to; the run's own exception is already the signal in that case).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A combination with a majority-failing recent history produces a visible warning
  on its next run, verified by an automated test.
- **SC-002**: A combination with a healthy history, or with too little history, produces no
  warning, verified by automated tests for both cases.
- **SC-003**: The check requires no new configuration or hardcoded model list — it is derived
  entirely from telemetry already being recorded (`ISS-013`).

## Assumptions

- A minimum sample size of 3 and a failure-rate threshold of 50% over the most recent 5 runs is
  a reasonable, conservative starting point — tunable later once real usage data accumulates,
  but chosen now specifically to avoid false positives from a single bad run (the exact false
  positive this project's own `ISS-009` incident could otherwise have caused if a fitness check
  had existed and reacted to one failure).
- The warning is surfaced as a plain text prefix on the skill's returned string, consistent with
  this codebase's existing convention of emoji-prefixed status messages (✅/❌ elsewhere) rather
  than a new structured warning channel.
