# py_mono/skill/telemetry.py
"""
Lightweight per-skill-run telemetry log (ISS-013).

Appends one flat JSON line per skill run to telemetry/skill_runs.jsonl:
    skill, provider, model, duration_ms, success, timestamp

Minimal by design: Milestone 6's model/task fitness check (ISS-014) and
Milestone 7's failure-driven evolution both need this same log — this is the
one place it's built, not duplicated per consumer. See docs/ROADMAP_PLAN.md.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

TELEMETRY_DIR = Path("telemetry")
TELEMETRY_LOG = TELEMETRY_DIR / "skill_runs.jsonl"


def log_skill_run(
    skill: str,
    provider: str,
    model: str,
    duration_ms: float,
    success: bool,
    request: str = "",
    failure_reason: str = "",
    log_path: Path = TELEMETRY_LOG,
) -> None:
    """Append one telemetry record as a JSON line.

    Never raises — a telemetry write failure (e.g. read-only filesystem)
    must never break skill execution, which is why every code path leading
    here is wrapped in a broad except.
    """
    record = {
        "skill": skill,
        "provider": provider,
        "model": model,
        "duration_ms": round(duration_ms, 2),
        "success": success,
        "request": request,
        "failure_reason": failure_reason,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")
    except OSError as e:
        logger.warning(f"Could not write telemetry record to {log_path}: {e}")


def read_skill_runs(log_path: Path = TELEMETRY_LOG) -> list[dict]:
    """Read all recorded telemetry records, skipping any corrupt lines
    rather than failing the whole read."""
    if not log_path.exists():
        return []

    records = []
    for line in log_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            logger.warning(f"Skipping corrupt telemetry line in {log_path}")
    return records
