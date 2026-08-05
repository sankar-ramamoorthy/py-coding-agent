# py_mono/skill/fitness.py
"""
Model/task fitness check (ISS-014).

Warns before returning a skill's result if telemetry (ISS-013) shows this
exact (skill, provider, model) combination has recently failed more often
than not. Productizes the ISS-009/ISS-011 lesson (thinking models reasoning
verbosely/unreliably on structured, template-filling tasks) as a general,
evidence-based check — driven by this repo's own recorded history, not a
hardcoded list of "bad" models.

Non-blocking by design: this only ever adds a warning banner to a skill's
result, never prevents execution. Requires at least MIN_SAMPLES prior
recorded runs for the exact combination before making any judgment, so a
single failure never triggers a false-positive warning.
"""

from pathlib import Path
from typing import Optional

from py_mono.skill.telemetry import TELEMETRY_LOG, read_skill_runs

MIN_SAMPLES = 3
RECENT_WINDOW = 5
FAILURE_RATE_THRESHOLD = 0.5


def check_model_fitness(
    skill: str,
    provider: str,
    model: str,
    log_path: Path = TELEMETRY_LOG,
) -> Optional[str]:
    """Return a warning string if this (skill, provider, model) combination
    has failed at least FAILURE_RATE_THRESHOLD of its most recent
    RECENT_WINDOW runs, else None.
    """
    records = read_skill_runs(log_path)
    matching = [
        r
        for r in records
        if r.get("skill") == skill
        and r.get("provider") == provider
        and r.get("model") == model
    ]

    if len(matching) < MIN_SAMPLES:
        return None

    recent = matching[-RECENT_WINDOW:]
    failures = sum(1 for r in recent if not r.get("success"))
    failure_rate = failures / len(recent)

    if failure_rate < FAILURE_RATE_THRESHOLD:
        return None

    return (
        f"⚠️ Fitness warning: skill '{skill}' has failed {failures}/{len(recent)} recent "
        f"runs with provider={provider} model={model}. This model may be a poor fit for "
        f"this task — consider switching providers/models (`/provider <name> [model]`)."
    )
