"""Diff helpers for generated skill review."""

from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path

from py_mono.skill import approval_ledger

CANDIDATE_DIRNAME = ".candidate"


@dataclass
class ApprovedBaseline:
    skill_name: str
    skill_md_content: str
    skill_py_content: str
    available: bool
    reason: str = ""


@dataclass
class ArtifactDiff:
    artifact: str
    changed: bool
    baseline_available: bool
    diff_text: str


def candidate_dir_for(skill_dir: Path) -> Path:
    return skill_dir / CANDIDATE_DIRNAME


def has_candidate(skill_dir: Path) -> bool:
    candidate_dir = candidate_dir_for(skill_dir)
    return (candidate_dir / "SKILL.md").exists() and (candidate_dir / "skill.py").exists()


def load_approved_baseline(skills_dir: Path, skill_name: str) -> ApprovedBaseline:
    skill_dir = skills_dir / skill_name
    skill_md = skill_dir / "SKILL.md"
    skill_py = skill_dir / "skill.py"
    if not skill_md.exists() or not skill_py.exists():
        return ApprovedBaseline(skill_name, "", "", False, "No existing skill files found.")

    ledger = approval_ledger.load_ledger(approval_ledger.ledger_path_for(skills_dir))
    if not approval_ledger.is_approved(ledger, skill_name, skill_py):
        return ApprovedBaseline(
            skill_name,
            "",
            "",
            False,
            "No approved baseline exists for the current skill.py content.",
        )

    return ApprovedBaseline(
        skill_name=skill_name,
        skill_md_content=skill_md.read_text(encoding="utf-8"),
        skill_py_content=skill_py.read_text(encoding="utf-8"),
        available=True,
    )


def build_artifact_diff(
    artifact: str,
    before: str,
    after: str,
    baseline_available: bool,
    missing_reason: str = "",
) -> ArtifactDiff:
    if not baseline_available:
        return ArtifactDiff(
            artifact=artifact,
            changed=False,
            baseline_available=False,
            diff_text=missing_reason or "No approved baseline available.",
        )

    if before == after:
        return ArtifactDiff(
            artifact=artifact,
            changed=False,
            baseline_available=True,
            diff_text=f"No changes in {artifact}.",
        )

    diff = difflib.unified_diff(
        before.splitlines(),
        after.splitlines(),
        fromfile=f"approved/{artifact}",
        tofile=f"candidate/{artifact}",
        lineterm="",
    )
    return ArtifactDiff(
        artifact=artifact,
        changed=True,
        baseline_available=True,
        diff_text="\n".join(diff),
    )


def render_diff_report(diffs: list[ArtifactDiff]) -> str:
    lines = ["Regeneration diff:"]
    for diff in diffs:
        lines.append(f"--- {diff.artifact} ---")
        if not diff.baseline_available:
            lines.append(f"Baseline unavailable: {diff.diff_text}")
        elif not diff.changed:
            lines.append(diff.diff_text)
        else:
            lines.append(diff.diff_text)
    return "\n".join(lines)


def write_candidate(skill_dir: Path, skill_md_content: str, skill_py_content: str) -> Path:
    candidate_dir = candidate_dir_for(skill_dir)
    candidate_dir.mkdir(parents=True, exist_ok=True)
    (candidate_dir / "SKILL.md").write_text(skill_md_content, encoding="utf-8")
    (candidate_dir / "skill.py").write_text(skill_py_content, encoding="utf-8")
    return candidate_dir


def promote_candidate(skill_dir: Path) -> bool:
    candidate_dir = candidate_dir_for(skill_dir)
    skill_md = candidate_dir / "SKILL.md"
    skill_py = candidate_dir / "skill.py"
    if not skill_md.exists() or not skill_py.exists():
        return False

    (skill_dir / "SKILL.md").write_text(skill_md.read_text(encoding="utf-8"), encoding="utf-8")
    (skill_dir / "skill.py").write_text(skill_py.read_text(encoding="utf-8"), encoding="utf-8")
    skill_md.unlink()
    skill_py.unlink()
    try:
        candidate_dir.rmdir()
    except OSError:
        pass
    return True
