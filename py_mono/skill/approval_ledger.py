# py_mono/skill/approval_ledger.py
"""
Approval ledger for skills.

Records, separately from each skill's own SKILL.md, a content hash of skill.py
at the moment it was approved. Load-time execution is gated on the ledger's
recorded hash matching the skill's CURRENT content — editing skill.py after
approval invalidates the entry until it is explicitly re-approved.

See docs/adr/ADR-013 (Skill Approval and Chaining Policy) and ISS-003.
"""

import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

logger = logging.getLogger(__name__)

LEDGER_FILENAME = ".approvals.json"


def ledger_path_for(skills_dir: Path) -> Path:
    """The ledger lives alongside the skills it tracks, not at a fixed global
    path — keeps ledger and skills_dir colocated, and keeps tests using a
    temporary skills_dir fully isolated from the real skills/.approvals.json."""
    return skills_dir / LEDGER_FILENAME


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_ledger(path: Path) -> Dict[str, dict]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read approval ledger {path}: {e}")
        return {}


def save_ledger(ledger: Dict[str, dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def is_approved(ledger: Dict[str, dict], skill_name: str, skill_py: Path) -> bool:
    """True only if the ledger has an entry for this skill whose recorded hash
    matches skill_py's CURRENT content — a hash mismatch (content changed
    since approval) is treated as not-approved, same as no entry at all."""
    entry = ledger.get(skill_name)
    if not entry or not skill_py.exists():
        return False
    return entry.get("sha256") == hash_file(skill_py)


def record_approval(
    ledger: Dict[str, dict],
    skill_name: str,
    skill_py: Path,
    seeded: bool = False,
) -> None:
    """Write/overwrite this skill's ledger entry with skill_py's current hash.

    seeded=True marks an entry written by the one-time auto-seed for a skill
    that was already status: approved before this ledger existed — this is a
    recognition of prior state, not a genuine review, and stays visibly
    distinguishable from a real /approve action (seeded=False).
    """
    ledger[skill_name] = {
        "sha256": hash_file(skill_py),
        "recorded_at": datetime.now(timezone.utc).isoformat(),
        "seeded": seeded,
    }
