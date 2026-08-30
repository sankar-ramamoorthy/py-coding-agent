from pathlib import Path

from py_mono.skill import approval_ledger
from py_mono.skill.diffing import (
    build_artifact_diff,
    has_candidate,
    load_approved_baseline,
    promote_candidate,
    render_diff_report,
    write_candidate,
)


def write_approved_skill(skills_dir: Path, name: str) -> Path:
    skill_dir = skills_dir / name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: demo\nstatus: approved\n---\n# Demo\n",
        encoding="utf-8",
    )
    (skill_dir / "skill.py").write_text("print('old')\n", encoding="utf-8")
    ledger = {}
    approval_ledger.record_approval(ledger, name, skill_dir / "skill.py")
    approval_ledger.save_ledger(ledger, approval_ledger.ledger_path_for(skills_dir))
    return skill_dir


def test_load_approved_baseline_reads_ledger_matched_files(tmp_path):
    write_approved_skill(tmp_path, "demo-skill")

    baseline = load_approved_baseline(tmp_path, "demo-skill")

    assert baseline.available is True
    assert "status: approved" in baseline.skill_md_content
    assert "print('old')" in baseline.skill_py_content


def test_load_approved_baseline_reports_hash_mismatch(tmp_path):
    skill_dir = write_approved_skill(tmp_path, "demo-skill")
    (skill_dir / "skill.py").write_text("print('changed')\n", encoding="utf-8")

    baseline = load_approved_baseline(tmp_path, "demo-skill")

    assert baseline.available is False
    assert "No approved baseline" in baseline.reason


def test_build_artifact_diff_renders_unified_diff():
    diff = build_artifact_diff("skill.py", "return 1\n", "return 2\n", True)

    assert diff.changed is True
    assert "--- approved/skill.py" in diff.diff_text
    assert "+++ candidate/skill.py" in diff.diff_text
    assert "-return 1" in diff.diff_text
    assert "+return 2" in diff.diff_text


def test_build_artifact_diff_reports_no_change():
    diff = build_artifact_diff("SKILL.md", "same\n", "same\n", True)

    assert diff.changed is False
    assert diff.diff_text == "No changes in SKILL.md."


def test_render_diff_report_identifies_missing_baseline():
    diff = build_artifact_diff("skill.py", "", "new\n", False, "missing")

    report = render_diff_report([diff])

    assert "Regeneration diff:" in report
    assert "Baseline unavailable: missing" in report


def test_write_and_promote_candidate(tmp_path):
    skill_dir = write_approved_skill(tmp_path, "demo-skill")

    candidate_dir = write_candidate(skill_dir, "candidate md", "candidate py")

    assert has_candidate(skill_dir) is True
    assert candidate_dir.name == ".candidate"
    assert promote_candidate(skill_dir) is True
    assert has_candidate(skill_dir) is False
    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "candidate md"
    assert (skill_dir / "skill.py").read_text(encoding="utf-8") == "candidate py"
